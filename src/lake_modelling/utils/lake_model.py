import os
from datetime import datetime, timedelta

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from scipy.integrate import odeint
from scipy.interpolate import interp1d

plt.style.use("ggplot")

LIME_PRODUCTS_DATA = "data/lime_products.xlsx"
FLOW_TYPES_DATA = "data/flow_typologies.xlsx"
TITRATION_CURVE_DATA = "data/titration_curves_interpolated.xlsx"


class Lake:
    def __init__(
        self,
        area=0.2,
        depth=5,
        tau=0.7,
        flow_prof="fjell",
        pH_lake0=4.5,
        toc_lake0=4,
    ):
        """Initialise lake object.

        Args
            area:         Float. Lake surface area (km2)
            depth:        Float. Lake mean depth (metres)
            tau:          Float. Lake mean annual residence time (years)
            flow_prof:    Str. Flow typology (typical monthly flow profile relative to
                          annual mean flow). Must be defined in 'flow_typologies.xlsx'
                          One of ('none', 'fjell', 'kyst')
            pH_lake0:     Float. Lake initial pH (dimensionless)
            toc_lake0:    Float. Lake initial TOC concentration (mg/l)

        Returns
            None.
        """
        # User-definied attributes
        self.area = area
        self.depth = depth
        self.tau = tau
        self.flow_prof = flow_prof
        self.pH_lake0 = pH_lake0
        self.toc_lake0 = toc_lake0
        self._validate_input()

        # Fixed attributes
        self.C_lake0 = 0
        self.C_in0 = 0
        self.C_bott = 0

    def _validate_input(self):
        """Check user-supplied values are reasonable."""
        gt0 = ("area", "depth", "tau")
        for attr in gt0:
            assert getattr(self, attr) > 0, f"'{attr}' must be greater than 0."
        assert self.flow_prof in (
            "none",
            "fjell",
            "kyst",
        ), "'flow_prof' must be one of ('none', 'fjell', 'kyst')."
        assert 4.5 <= self.pH_lake0 <= 6.5, "'pH_lake0' must be between 4.5 and 6.5."
        assert self.toc_lake0 >= 0, "'toc_lake0' must be greater than or equal to 0."

    @property
    def volume(self):
        """Lake volume in litres from surface area and mean depth."""
        return 1000 * self.area * 1e6 * self.depth

    @property
    def mean_annual_flow(self):
        """Mean annual flow (in litres/month) from lake volume and residence time."""
        return round(self.volume / (12 * self.tau), 0)

    @property
    def monthly_flows(self):
        """Monthly flows (in litres/month) based on mean annual flow and flow typology."""
        xl_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), f"../../../{FLOW_TYPES_DATA}"
        )
        q_df = (pd.read_excel(xl_path, index_col=0) * self.mean_annual_flow).round(0)
        q_dict = q_df[self.flow_prof].to_dict()

        return q_dict

    def plot_flow_profile(self, lib):
        """Plot monthly flows.

        Args
            lib: Str. Plotting library to use. Either 'Altair' or 'Matplotlib'.

        Returns
            Chart object. The chart is also added to the Streamlit app if Streamlit
            is running.
        """

        months = range(1, 13)
        q_lpmon = np.array([self.monthly_flows[i] for i in months])
        q_m3ps = q_lpmon / (1000 * 60 * 60 * 24 * 30)
        q_mean = self.mean_annual_flow / (1000 * 60 * 60 * 24 * 30)

        if lib == "Matplotlib":
            plt.plot(months, q_m3ps, "ro-")
            plt.axhline(q_mean, c="k", ls="--", label="Annual mean")
            plt.xlabel("Month")
            plt.ylabel("Discharge ($m^3/s$)")
            plt.legend()
            st.set_option("deprecation.showPyplotGlobalUse", False)
            st.pyplot()

        else:
            df_long_form = pd.DataFrame(
                {
                    "Month": [
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        12,
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        12,
                    ],
                    "Flow": ["Monthly flow"] * 12 + ["Annual mean"] * 12,
                    "Discharge (m\u00b3/s)": q_m3ps.tolist() + [q_mean] * 12,
                }
            )
            chart = (
                alt.Chart(df_long_form)
                .mark_line(point=True)
                .encode(
                    alt.X("Month:N", axis=alt.Axis(labelAngle=0)),
                    y="Discharge (m\u00b3/s):Q",
                    color="Flow:N",
                    strokeDash=alt.condition(
                        alt.datum.Flow == "Annual mean",
                        alt.value(
                            [8, 8]
                        ),  # dashed line: 5 pixels  dash + 5 pixels space
                        alt.value([0]),  # solid line
                    ),
                    tooltip=[
                        "Month:N",
                        alt.Tooltip("Discharge (m\u00b3/s):Q", format=",.2f"),
                        "Flow:N",
                    ],
                )
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)

            return chart


class LimeProduct:
    def __init__(self, name, from_database=True, **kwargs):
        """Initialise lime product object. If 'from_database' is True, lime
        properties are loaded from the database. Otherwise, all necessary
        parameters must be provided as 'kwargs'.

        NOTE: If 'from_database' is True, all 'kwargs' are ignored.

        Args
            name:          Str. Name of lime product
            from_database: Bool. If True, lime properties are loaded from
                           the database.

        Kwargs (only used if from_database=False)
            ca_pct:        Float. Percentage of Ca (NOT CaCO3) by mass
            mg_pct:        Float. Percentage of Mg (NOT MgCO3) by mass
            dry_fac:       Float. Between 0 and 1. Factor to apply for 'dry'
                           spreading
            col_depth:     Float. Length of columns used (in metres)
            id_list:       List of floats. Instantaneous dissolution in percent
                           for fixed lime dose of 10 mg/l at varying pH
                           (4.0, 4.5, 5.0, 5.5, 6.0)
            od_list:       List of floats. Overdosing factors for pH fixed at
                           4.6 and varying lime doses of
                           (10, 20, 35, 50, 85) mg/l
        """
        self._name = name
        if from_database:
            self._get_lime_properties(name)
        else:
            req_attrs = (
                "ca_pct",
                "mg_pct",
                "dry_fac",
                "col_depth",
                "id_list",
                "od_list",
            )
            for attr in req_attrs:
                try:
                    setattr(self, attr, kwargs[attr])
                except KeyError:
                    raise KeyError(
                        f"'{attr}' is a required keyword argument when 'from_database' is False."
                    )
        self._validate_input()

    def _validate_input(self):
        """Check user-supplied values are reasonable."""
        assert (
            0 <= self.ca_pct <= 40
        ), "'ca_pct' must be between 0 and 40 (pure CaCO3 is 40% Ca)."
        assert (
            0 <= self.mg_pct <= 29
        ), "'mg_pct' must be between 0 and 29 (pure MgCO3 is 29% Mg)."
        assert 0 <= self.dry_fac <= 1, "'dry_fac' must be between 0 and 1."
        assert 1 <= self.col_depth <= 10, "'col_depth' must be between 1 and 10."
        assert len(self.id_list) == 5, "'id_list' should contain 5 values."
        assert len(self.od_list) == 5, "'od_list' should contain 5 values."

    def _get_lime_properties(self, name):
        """Read lime properties from the database and adds them as attributes.

        Args
            name: Str. Name of lime product.

        Returns
            None. Attributes are updated
        """
        xl_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            f"../../../{LIME_PRODUCTS_DATA}",
        )
        df = pd.read_excel(xl_path, index_col=0)
        if name not in df.columns:
            raise KeyError(f"Lime product '{name}' not found in database.")

        self.ca_pct = df.loc["CaPct", name]
        self.mg_pct = df.loc["MgPct", name]
        self.dry_fac = df.loc["DryFac", name]
        self.col_depth = df.loc["ColDepth", name]
        self.id_list = [df.loc[f"IDph{ph}", name] for ph in (40, 45, 50, 55, 60)]
        self.od_list = [df.loc[f"OD{dose}", name] for dose in (10, 20, 35, 50, 85)]

    def get_instantaneous_dissolution(self, pH, dose):
        """Interpolates column test data to estimate the instantaneous dissolution (ID)
        for the given pH and lime dose. First interpolates ID values for dose = 10 mg/l
        for the desired pH, then interpolates overdosing factors (ODs) for pH = 4.6 for
        the desired dose. These are then combined to give the estimated ID.

        NOTE: This function performs interpolation, not extrapolation. Permitted pH
        ranges are 4 to 6 and dose ranges are 10 to 85 mg/l. Values outside this range
        will return ID values for the nearest boundary.

        Args
            pH:   Float. pH at which ID is to be estimated
            dose: Float. Lime dose (in mg/l) at which ID is to be estimated

        Returns
            Float. Estimated instananeous dissolution in percent.
        """
        # Clip data to interpolation range
        pH = max(min(pH, 6), 4)
        dose = max(min(dose, 85), 10)

        # Interpolate ID at dose = 10 mg/l
        interp_ph = interp1d([4, 4.5, 5, 5.5, 6], self.id_list)
        id_d10 = interp_ph(pH)

        # Interpolate OD at pH = 4.6
        interp_od = interp1d([10, 20, 35, 50, 85], self.od_list)
        od_ph46 = interp_od(dose)

        return id_d10 / od_ph46

    def plot_column_data(self, lib):
        """Plot column test data.

        Args
            lib: Str. Plotting library to use. Either 'Altair' or 'Matplotlib'.

        Returns
            Chart object. The chart is also added to the Streamlit app if Streamlit
            is running.
        """

        if lib == "Matplotlib":
            fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(8, 4))

            # ID values at dose = 10 mg/l
            axes[0].plot([4, 4.5, 5, 5.5, 6], self.id_list, "ro-")
            axes[0].set_ylim(bottom=0)
            axes[0].set_title(
                f"{self.col_depth} m column; 10 mg/l of lime", fontsize=14
            )
            axes[0].set_ylabel("Instantaneous dissolution (%)")
            axes[0].set_xlabel("Column pH (-)")

            # OD values at pH 4.6
            axes[1].plot([10, 20, 35, 50, 85], self.od_list, "ro-")
            axes[1].set_ylim(bottom=0)
            axes[1].set_title(f"{self.col_depth} m column; pH 4.6", fontsize=14)
            axes[1].set_ylabel("Overdosing factor (-)")
            axes[1].set_xlabel("Lime dose (mg/l)")

            fig.suptitle(self._name, fontsize=16)
            plt.tight_layout()
            st.set_option("deprecation.showPyplotGlobalUse", False)
            st.pyplot()
        else:
            inst_diss = pd.DataFrame(
                {
                    "Column pH (-)": [4, 4.5, 5, 5.5, 6],
                    "Instantaneous dissolution (%)": self.id_list,
                }
            )
            inst_chart = (
                alt.Chart(
                    inst_diss, title=f"{self.col_depth} m column; 10 mg/l of lime"
                )
                .mark_line(point=True)
                .encode(
                    x="Column pH (-)",
                    y="Instantaneous dissolution (%)",
                    tooltip=["Column pH (-)", "Instantaneous dissolution (%)"],
                )
                .properties(width=250, height=200)
                .interactive()
            )
            over_fac = pd.DataFrame(
                {
                    "Lime dose (mg/l)": [10, 20, 35, 50, 85],
                    "Overdosing factor (-)": self.od_list,
                }
            )
            over_chart = (
                alt.Chart(over_fac, title=f"{self.col_depth} m column; pH 4.6")
                .mark_line(point=True)
                .encode(
                    x="Lime dose (mg/l)",
                    y="Overdosing factor (-)",
                    tooltip=["Lime dose (mg/l)", "Overdosing factor (-)"],
                )
                .properties(width=250, height=200)
                .interactive()
            )
            chart = alt.hconcat(
                inst_chart, over_chart, title=self._name
            ).configure_title(anchor="middle")
            st.altair_chart(chart, use_container_width=True)

            return chart


class Model:
    def __init__(
        self,
        lake,
        lime_product,
        lime_dose=10,
        lime_month=1,
        spr_meth="wet",
        spr_prop=0.5,
        F_sol=1,
        rate_const=1,
        activity_const=0.1,
        ca_aq_sat=8.5,
        n_months=24,
    ):
        """Initialise model object.

        Args
            lake:           Obj. Instance of Lake class
            lime_product:   Obj. Instance of LimeProduct class
            lime_dose:      Float. Lime dose added (in mg/l)
            lime_month:     Int between 1 and 12. Month in which lime is added
            spr_meth:       Str. Liming method. Either 'wet' or 'dry'
            spr_prop:       Float between 0 and 1. Fraction of lake surface area that is limed
            F_sol:          Float. Proportion of lake-bottom lime that remains soluble
            rate_const:     Float. Parameter controlling the initial dissolution rate of lake-bottom lime
            activity_const: Float. Parameter controlling the rate that lake-bottom lime becomes inactive
            ca_aq_sat:      Float. Maximum Ca concentration (in mg-Ca/l) for a "saturated" solution. Used
                            to limit dissolution of lake-bottom lime when Ca concentrations become high
            n_months:       Int. Number of months to simulate, starting at 'lime_month'
        """
        # User-defined attributes
        self.lake = lake
        self.lime_product = lime_product
        self.lime_dose = lime_dose
        self.lime_month = lime_month
        self.spr_meth = spr_meth
        self.spr_prop = spr_prop
        self.F_sol = F_sol
        self.rate_const = rate_const
        self.activity_const = activity_const
        self.ca_aq_sat = ca_aq_sat
        self.n_months = n_months
        self._validate_input()

    def _validate_input(self):
        """Check user-supplied values are reasonable."""
        assert isinstance(self.lake, Lake), "'lake' must be a Lake object."
        assert isinstance(
            self.lime_product, LimeProduct
        ), "'lime_product' must be a LimeProduct object."
        assert 0 <= self.lime_dose <= 85, "'lime_dose' must be between 0 and 85 mg/l."
        assert isinstance(self.lime_month, int) and (
            1 <= self.lime_month <= 12
        ), "'lime_month' must be an integer between 1 and 12."
        assert self.spr_meth in (
            "wet",
            "dry",
        ), "'spr_meth' must be either 'wet' or 'dry'."
        assert 0 <= self.spr_prop <= 1, "'spr_prop' must be between 0 and 1."
        assert 0 <= self.F_sol <= 1, "'F_sol' must be between 0 and 1."
        assert self.rate_const >= 0, "'rate_const' must be greater than or equal to 0."
        assert (
            self.activity_const >= 0
        ), "'activity_const' must be greater than or equal to 0."
        assert self.ca_aq_sat > 0, "'ca_aq_sat' must be greater than 0."
        assert isinstance(self.n_months, int) and (
            self.n_months > 1
        ), "'n_months' must be an integer greater than 1."

    @property
    def method_fac(self):
        """Get the factor applied to the instantaneous dissolution to allow for
        the spreading method (value between 0 and 1).
        """
        if self.spr_meth == "wet":
            return 1
        else:
            return self.lime_product.dry_fac

    @property
    def C_inst0(self):
        """Total instantaneous dissolution in Ca-equivalents (mg/l), allowing for
        the proportion of the lake surface that is limed.
        """
        return self.spr_prop * self._partition_lime_equivalents()[0]

    @property
    def C_bott0(self):
        """Soluble lake-bottom lime in Ca-equivalents (mg/l), allowing for
        the proportion of the lake surface that is limed.
        """
        return self.spr_prop * self._partition_lime_equivalents()[1]

    def _get_effective_ph_for_depth(self, par):
        """To generalise the column test data to lakes with different depths, a
        correction is applied such that the dissolution in a lake of depth d_lake
        is assumed equal to the dissolution in a column of depth d_col with a
        modified pH. The correction is slightly different for Ca versus Mg.

        Args
            par: Either 'Ca' or 'Mg'

        Returns
            Floats. Effective pH use to query ID data from column test results
            for 'par'.
        """
        assert par in ("Ca", "Mg"), "'par' must be either 'Ca'or 'Mg'."

        depth_corr = np.log10(self.lake.depth / self.lime_product.col_depth)
        if par == "Ca":
            return self.lake.pH_lake0 - depth_corr
        else:
            return self.lake.pH_lake0 - 0.5 * depth_corr

    def _partition_lime_equivalents(self):
        """Estimate the instantaneous dissolution of the Ca and Mg componets.
        Convert Mg to Ca-equivalents and partition into two fractions: one that
        dissolves "instantly" and another that sinks to the bottom but remains
        available for slow dissolution.

        Args
            None

        Returns
            Tuple of floats (C_inst, C_bott). C_inst is the "instantaneous" increase
            in lake Ca concentration (in mg/l of Ca-equivalents) due to rapid
            dissolution of CaCO3 and MgCO3; C_bott is the remainder of the lime
            (also in mg/l of Ca-equivalents) that sinks to the bottom of the lake
            and remains available for dissolution.
        """
        # Molar masses
        # MM_MgCO3 = 84.31
        # MM_CaCO3 = 100.09
        MM_Mg = 24.31
        MM_Ca = 40.08

        # Get dose of Ca and Mg
        ca_dose = self.lime_product.ca_pct * self.lime_dose / 100
        mg_dose = self.lime_product.mg_pct * self.lime_dose / 100

        # Get instantaneous dissolution
        eff_ph_ca = self._get_effective_ph_for_depth("Ca")
        eff_ph_mg = self._get_effective_ph_for_depth("Mg")
        id_ca_pct = self.method_fac * self.lime_product.get_instantaneous_dissolution(
            eff_ph_ca, self.lime_dose
        )
        id_mg_pct = self.method_fac * self.lime_product.get_instantaneous_dissolution(
            eff_ph_mg, self.lime_dose
        )

        # Partition between water column and lake bottom
        id_ca = id_ca_pct * ca_dose / 100
        id_mg = id_mg_pct * mg_dose / 100
        bott_ca = ca_dose - id_ca
        bott_mg = mg_dose - id_mg

        # Convert to Ca-equivalents
        C_inst0 = id_ca + (id_mg * MM_Ca / MM_Mg)
        C_bott0 = self.F_sol * (bott_ca + (bott_mg * MM_Ca / MM_Mg))

        return (C_inst0, C_bott0)

    def _pH_from_delta_Ca(self):
        """Build a titration curve linking change in Ca-equivalents to lake pH."""
        # Get TOC class
        if self.lake.toc_lake0 <= 3:
            toc_class = "TOC ≤ 3"
        elif 3 < self.lake.toc_lake0 <= 5:
            toc_class = "3 < TOC ≤ 5"
        else:
            toc_class = "TOC > 5"

        # Build interpolator
        xl_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            f"../../../{TITRATION_CURVE_DATA}",
        )
        df = pd.read_excel(xl_path)
        df = df.query("`TOC class (mg/l)` == @toc_class")
        interp_ph = interp1d(
            df["pH"].values, df["CaCO3 (mg/l)"].values, fill_value="extrapolate"
        )
        interp_ca = interp1d(
            df["CaCO3 (mg/l)"].values, df["pH"].values, fill_value="extrapolate"
        )

        # Convert modelled change in Ca to abs. conc. of CaCO3
        delta_caco3_mod = self.model_delta_ca_mgpl * 100.09 / 40.08
        caco3_0 = interp_ph(self.lake.pH_lake0)
        caco3_mod = caco3_0 + delta_caco3_mod

        # Predict pH from modelled CaCO3
        ph_mod = interp_ca(caco3_mod)

        return ph_mod

    def run(self, dt=0.01):
        """Simulate change in concentration of Ca-equivalents and pH over time.

        Args
            dt: Float between 0 and 1 (months). Time resolution in decimal
                months for evaluating the model within each monthly time step.
                NOTE: This parameter does not affect how the ODEs are solved
                (that is handled automatically). It simply sets the level of
                temporal detail in the output. Larger values run faster, but
                give coarser output.
        """

        def dCdt(y, t, params):
            """Define the ODE system.

            Args
                y:      List. [C_lake]. Current lake Ca concentration in mg/l of Ca-
                        equivalents
                t:      Array. Time points at which to evaluate C_lake (in months)
                params: Tuple. (Q, V, C_in, rate_const, activity_const, ca_aq_sat).
                            'Q' is mean flow in litres/month
                            'V' is lake volume in litres
                            'C_in' in lake inflow concentration of Ca in mg/l
                            'rate_const' determines the initial rate of dissoltuion of lime
                            on the bottom of the lake (months^-1)
                            'activity_const' determines how rapidly lake bottom limes
                            becomes inactive (months^-1)
                            'ca_aq_sat' is the maximum Ca concentration (in mg-Ca/l) for a
                            saturated solution

            Returns
                Array.
            """
            # Unpack incremental value for C_lake
            C_lake, C_bott = y

            # Unpack fixed params
            Q, V, C_in, rate_const, activity_const, ca_aq_sat = params

            # Time-dependent first-order rate constant for lake-bottom lime
            k = rate_const * np.exp(-activity_const * t)

            # Sigmoid function to reduce reaction rate as the solution approaches saturation
            rate_factor = 1 / (1 + np.exp(10 * (C_lake - ca_aq_sat)))

            # Assume simple 1st order reaction for dissolution of lake-bottom CaCO3
            # modified to include declining lime "activity" over time and to stop
            # dissolution if C_lake is near saturation
            dCbott_dt = -k * rate_factor * min(C_bott, (ca_aq_sat - C_lake))

            # Lake conc. depends on flow regime and amount of lake bottom lime that dissolves
            # Note (-1 * dCbott_dt) because dCbott_dt is negative
            dClake_dt = (Q * C_in - Q * C_lake) / V - dCbott_dt

            dydt = [dClake_dt, dCbott_dt]

            return dydt

        # Setup time domain
        assert 0 < dt < 1, "'dt' must be between 0 and 1."
        months = range(self.n_months)
        month_ids = (list(range(1, 13)) * self.n_months)[
            self.lime_month - 1 : self.lime_month + self.n_months
        ]
        self.dt = dt
        self.month_ids = month_ids

        # Loop over months
        C_bott = self.C_bott0
        C_lake = self.lake.C_lake0 + self.C_inst0
        ys = []
        tis = []
        for month in months:
            # Get flow this month
            month_id = month_ids[month]
            q_month = self.lake.monthly_flows[month_id]

            # Solve ODEs
            y0 = [C_lake, C_bott]
            params = [
                q_month,
                self.lake.volume,
                self.lake.C_in0,
                self.rate_const,
                self.activity_const,
                self.ca_aq_sat,
            ]
            ti = np.linspace(month, month + 1, num=int(1 + 1 / dt))
            y = odeint(dCdt, y0, ti, args=(params,))
            ys.append(y)
            tis.append(ti)

            # Update initial conditions for next step
            C_lake, C_bott = y[-1]

        # Build df from output
        df = pd.DataFrame(
            data=np.concatenate(ys),
            columns=["Delta Ca (mg/l)", "Delta Ca bottom (mg/l)"],
            index=np.concatenate(tis),
        )
        del df["Delta Ca bottom (mg/l)"]

        # At each time step, the solver runs from month to (month + 1) inclusive.
        # The first and last time points in successive segments are therefore
        # duplicated. Remove these. Also shift month index by 'lime_month' so
        # results start at correct month.
        df = df[~df.index.duplicated(keep="last")]
        df.index = df.index + self.lime_month - 1

        self.model_time_months = df.index.values
        self.model_delta_ca_mgpl = df["Delta Ca (mg/l)"].values

        # Convert delta Ca to pH
        ph_mod = self._pH_from_delta_Ca()
        df["pH"] = ph_mod
        self.model_lake_ph = ph_mod

        # Convert decimal months to dates for convenience. Use 2000 as an
        # arbitrary start year i.e only month and day have any meaning
        df["date"] = datetime(2000, 1, 1) + pd.to_timedelta(
            df.index * 365 / 12, unit="D"
        )
        df = df[["date", "Delta Ca (mg/l)", "pH"]]
        self.result_df = df

        return df

    def plot_result(self, lib):
        """Plot results.

        Args
            lib: Str. Plotting library to use. Either 'Altair' or 'Matplotlib'.

        Returns
            Chart object. The chart is also added to the Streamlit app if Streamlit
            is running.
        """
        # Make sure results are up-to-date
        df = self.run().copy()
        df.set_index("date", inplace=True)
        df = df.resample("D").mean()

        if lib == "Matplotlib":
            # Matplotlib charts
            axes = df.plot(subplots=True, legend=False, title=self.lime_product._name)
            axes[0].set_ylim(bottom=0)
            axes[1].axhline(y=self.lake.pH_lake0, ls="--", c="k")
            axes[0].set_ylabel("$\Delta Ca_{ekv}$ (mg/l)")
            axes[1].set_ylabel("Lake pH (-)")
            axes[1].set_xlabel("")
            plt.tight_layout()
            st.set_option("deprecation.showPyplotGlobalUse", False)
            st.pyplot()
        else:
            # Altair charts
            df.reset_index(inplace=True)
            init_ph = (
                alt.Chart(pd.DataFrame({"pH": [self.lake.pH_lake0]}))
                .mark_rule(strokeDash=[10, 10])
                .encode(y="pH")
            )
            ph_chart = (
                alt.Chart(df)
                .mark_line()
                .encode(
                    x=alt.X("date", axis=alt.Axis(title="Months", grid=True)),
                    y=alt.Y(
                        "pH",
                        axis=alt.Axis(title="Lake pH (-)"),
                        scale=alt.Scale(zero=False),
                    ),
                    tooltip=["date", alt.Tooltip("pH", format=",.2f")],
                )
                .properties(width=600, height=200)
                .interactive()
            )
            ca_chart = (
                alt.Chart(df)
                .mark_line()
                .encode(
                    x=alt.X(
                        "date",
                        axis=alt.Axis(title=" ", grid=True),
                    ),
                    y=alt.Y(
                        "Delta Ca (mg/l)",
                        axis=alt.Axis(title="\u0394Ca\u2091\u2096\u1D65 (mg/l)"),
                        # scale=alt.Scale(zero=False),
                    ),
                    tooltip=["date", alt.Tooltip("Delta Ca (mg/l)", format=",.2f")],
                )
                .properties(width=600, height=200)
                .interactive()
            )
            chart = alt.vconcat(ca_chart, ph_chart + init_ph)
            st.altair_chart(chart, use_container_width=True)

            return chart
