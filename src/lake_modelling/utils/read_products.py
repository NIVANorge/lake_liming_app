import pandas as pd


def get_lime_products(path):
    products = pd.read_excel(path, index_col=0).to_dict()
    del products["Description"]
    return products


def get_lime_product_names(products):
    prod_names = [*products]
    return prod_names
