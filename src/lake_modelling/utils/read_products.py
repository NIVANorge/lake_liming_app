import pandas as pd


def lime_products(path):
    products = pd.read_excel(path, index_col=0).to_dict()
    del products["Description"]
    return products


def lime_product_names(products):
    prod_names = sorted([*products])
    return prod_names