from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import odeint
from scipy.interpolate import interp1d

plt.style.use("ggplot")


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
        q_df = (
            pd.read_excel("../data/flow_typologies.xlsx", index_col=0)
            * self.mean_annual_flow
        ).round(0)
        q_dict = q_df[self.flow_prof].to_dict()

        return q_dict

    # @property
    # def pH_0(self):
    #     return self._get_pH0_ApH()[0]

    # @property
    # def A_pH(self):
    #     return self._get_pH0_ApH()[1]

    # def _get_pH0_ApH(self):
    #     """Determine pH_0 and A_pH from lake colour and initial pH. These parameters
    #     determine the titration curve used to predict how changes in Ca concentration
    #     affect lake pH. Modified from Table 2 of the TPKALK report:

    #     https://niva.brage.unit.no/niva-xmlui/bitstream/handle/11250/208709/3412_200dpi.pdf?sequence=2&isAllowed=y#page=11

    #     Args
    #         None

    #     Returns
    #         Tuple (pH_0, A_pH)
    #     """
    #     # Based on Table 2 dict[(lake_ph, lake_colour)] => (pH_0, A_pH)
    #     data_dict = {
    #         ("<5", ">=0to<1"): (3.5, 1.5),
    #         ("<5", ">=1to<5"): (3.5, 1.5),
    #         ("<5", ">=5to<20"): (3.5, 1.5),
    #         ("<5", ">=20"): (None, None),
    #         (">=5", ">=0to<1"): (3.5, 1.8),
    #         (">=5", ">=1to<5"): (3.9, 1.2),
    #         (">=5", ">=5to<20"): (None, None),
    #         (">=5", ">=20"): (4.3, 0.7),
    #     }

    #     # Get colour class
    #     bins = [0, 1, 5, 20, 1e3]
    #     labels = [">=0to<1", ">=1to<5", ">=5to<20", ">=20"]
    #     col_class = pd.cut([self.colour_lake0], bins, labels=labels, right=False)[0]

    #     # Get pH class
    #     if self.pH_lake0 < 5:
    #         pH_class = "<5"
    #     else:
    #         pH_class = ">=5"

    #     # Get pH_0 and A_pH
    #     pH_0, A_pH = data_dict[pH_class, col_class]
    #     if pH_0:
    #         return (pH_0, A_pH)
    #     else:
    #         raise ValueError(
    #             "'pH_0' and 'A_pH' are undefined for lakes with the specified initial pH and colour."
    #         )

    def plot_flow_profile(self):
        """Plot monthly flows using Matplotlib.

        TO DO: Generalise to take an argument that switches between
        Matplotlib and Altair.
        """
        months = range(1, 13)
        q_lpmon = np.array([self.monthly_flows[i] for i in months])
        q_m3ps = q_lpmon / (1000 * 60 * 60 * 24 * 30)
        q_mean = self.mean_annual_flow / (1000 * 60 * 60 * 24 * 30)
        plt.plot(months, q_m3ps, "ro-")
        plt.axhline(q_mean, c="k", ls="--", label="Annual mean")
        plt.xlabel("Month")
        plt.ylabel("Discharge ($m^3/s$)")
        plt.legend()


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
        assert 0 <= self.ca_pct <= 100, "'ca_pct' must be between 0 and 100."
        assert 0 <= self.mg_pct <= 100, "'mg_pct' must be between 0 and 100."
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
        df = pd.read_excel("../data/lime_products.xlsx", index_col=0)
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

    def plot_column_data(self):
        """Plot column test data using Matplotlib.

        TO DO: Generalise to take an argument that switches between
        Matplotlib and Altair.
        """
        fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(8, 4))

        # ID values at dose = 10 mg/l
        axes[0].plot([4, 4.5, 5, 5.5, 6], self.id_list, "ro-")
        axes[0].set_ylim(bottom=0)
        axes[0].set_title(f"{self.col_depth} m column; 10 mg/l of lime", fontsize=14)
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


class Model:
    def __init__(
        self,
        lake,
        lime_product,
        lime_dose=10,
        lime_month=1,
        spr_meth="wet",
        spr_prop=0.5,
        F_sol=0.4,
        K_L=1,
        n_months=24,
    ):
        """Initialise model object.

        Args
            lake:         Obj. Instance of Lake class
            lime_product: Obj. Instance of LimeProduct class
            lime_dose:    Float. Lime dose added (in mg/l)
            lime_month:   Int between 1 and 12. Month in which lime is added
            spr_meth:     Str. Liming method. Either 'wet' or 'dry'
            spr_prop:     Float between 0 and 1. Fraction of lake surface area that is limed
            F_sol:        Float. Proportion of lake-bottom lime that remains soluble
            K_L:          Float. Parameter controlling the dissolution rate of lake-bottom lime
            n_months:     Int. Number of months to simulate, starting at 'lime_month'
        """
        # User-defined attributes
        self.lake = lake
        self.lime_product = lime_product
        self.lime_dose = lime_dose
        self.lime_month = lime_month
        self.spr_meth = spr_meth
        self.spr_prop=spr_prop
        self.F_sol = F_sol
        self.K_L = K_L
        self.n_months = n_months
        self._validate_input()

    def _validate_input(self):
        """Check user-supplied values are reasonable."""
        assert isinstance(self.lake, Lake), "'lake' must be a Lake object."
        assert isinstance(
            self.lime_product, LimeProduct
        ), "'lime_product' must be a LimeProduct object."
        assert self.lime_dose > 0, "'lime_dose' must be greater than 0."
        assert isinstance(self.lime_month, int) and (
            1 <= self.lime_month <= 12
        ), "'lime_month' must be an integer between 1 and 12."
        assert self.spr_meth in (
            "wet",
            "dry",
        ), "'spr_meth' must be either 'wet' or 'dry'."
        assert 0 <= self.spr_prop <= 1, "'spr_prop' must be between 0 and 1."
        assert 0 <= self.F_sol <= 1, "'F_sol' must be between 0 and 1."
        assert self.K_L > 0, "'K_L' must be greater than 0."
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
            dissolution of CaCO3 and MgCo3; C_bott is the remainder of the lime
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
        """Build a titration curve linking change in Ca-equivalents to lake pH.
        """
        # Get TOC class
        if self.lake.toc_lake0 <= 3:
            toc_class = "TOC ≤ 3"
        elif 3 < self.lake.toc_lake0 <= 5:
            toc_class = "3 < TOC ≤ 5"
        else:
            toc_class = "TOC > 5"

        # Build interpolator
        df = pd.read_excel("../data/titration_curves_interpolated.xlsx")
        df = df.query("`TOC class (mg/l)` == @toc_class")
        interp_ph = interp1d(df['pH'].values, df['CaCO3 (mg/l)'].values, fill_value="extrapolate")
        interp_ca = interp1d(df['CaCO3 (mg/l)'].values, df['pH'].values, fill_value="extrapolate")

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
                params: Tuple. (Q, V, C_in, C_bott, K_L).
                            Q is mean flow in litres/month
                            V is lake volume in litres
                            C_in in lake inflow concentration of Ca in mg/l
                            C_bott is the 'dose' of lime on the lake bottom in mg-Ca/l
                            K_L determines the rate of dissoltuion of lime on the bottom
                            of the lake (months^-1)

            Returns
                Array.
            """
            # Unpack incremental value for C_lake
            C_lake = y[0]

            # Unpack fixed params
            Q, V, C_in, C_bott0, K_L = params

            # Model equations
            dCslow_dt = C_bott0 * K_L * np.exp(-K_L * t)
            dClake_dt = (Q * C_in - Q * C_lake) / V + dCslow_dt

            # Add results of equations to an array
            res = np.array([dClake_dt])

            return res

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
            y0 = [C_lake]
            params = [
                q_month,
                self.lake.volume,
                self.lake.C_in0,
                self.C_bott0,
                self.K_L,
            ]
            ti = np.linspace(month, month + 1, num=int(1 + 1 / dt))
            y = odeint(dCdt, y0, ti, args=(params,))
            y = y[:, 0]
            ys.append(y)
            tis.append(ti)

            # Update initial conditions for next step
            C_lake = y[-1]

        # Build df from output
        df = pd.DataFrame(
            data=np.concatenate(ys),
            columns=["Delta Ca (mg/l)"],
            index=np.concatenate(tis),
        )

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
        # df = df.round(2)
        self.result_df = df

        return df

    def plot_result(self):
        """Plot results using Matplotlib.

        TO DO: Generalise to take an argument that switches between
        Matplotlib and Altair.
        """
        # Make sure results are up-to-date
        self.run()
        df = self.result_df.copy()
        df.set_index("date", inplace=True)
        df = df.resample("D").mean()
        axes = df.plot(subplots=True, legend=False, title=self.lime_product._name)
        axes[0].set_ylim(bottom=0)
        axes[1].axhline(y=self.lake.pH_lake0, ls='--', c='k')
        axes[0].set_ylabel("$\Delta Ca_{ekv}$ (mg/l)")
        axes[1].set_ylabel("Lake pH (-)")
        axes[1].set_xlabel("")
        plt.tight_layout()
