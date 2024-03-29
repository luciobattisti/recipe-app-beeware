"""
Application to turn recipes into a shopping list
"""

import pint
import json
import toga
import os
from pathlib import Path
import shutil
import sys
from collections import Counter
from recipeapp.db.sqlite_helper.SQLiteHelper import SQLiteHelper
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER

# Utility section ################################################################

flatten: list = lambda l: [item for sublist in l for item in sublist]
is_android: bool = hasattr(sys, 'getandroidapilevel')

def most_common(l: list) -> any:
        """
        Return most common element from list.
        
        :param lst: Input list
        :type list: `list`
        :return: Most common item in list
        """
        data = Counter(l)

        return data.most_common(1)[0][0]

##################################################################################

# Main class
class RecipeApp(toga.App):
    
    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """

        ureg = pint.UnitRegistry()
        self.units = {
            "tbs": ureg.tbs,
            "fl oz": ureg.floz,
            "gill": ureg.gill,
            "cup": ureg.cup,
            "pt": ureg.pt,
            "qt": ureg.qt,
            "gal": ureg.gal,
            "lb": ureg.lb,
            "oz": ureg.oz,
            "": None
        }

        # android_path = "/data/data/com.example.recipeapp/files"

        db_fname = "recipe.db"
        db_res_fpath = f"{self.paths.app}/resources/{db_fname}"
        db_fpath = f"{self.paths.data}/{db_fname}"

        # if is_android:
        #    db_fpath = f"{android_path}/{db_fname}"
        # else:
        #    db_fpath = f"{self.paths.data}/{db_fname}"

        selections_fname = "selections.json"        
        selections_res_fpath = f"{self.paths.app}/resources/{selections_fname}"
        selections_fpath = f"{self.paths.data}/{selections_fname}"

        # if is_android:
        #     selections_fpath = f"{android_path}/{selections_fname}"
        # else:    
        #     selections_fpath = f"{self.paths.data}/{selections_fname}"

        os.makedirs(self.paths.data, exist_ok=True)
        
        if not Path(db_fpath).is_file():
            shutil.copyfile(db_res_fpath, db_fpath)

        if not Path(selections_fpath).is_file():
            shutil.copyfile(selections_res_fpath, selections_fpath)

        print(f"{self.paths.data}/{db_fname}")
        self.db_helper = SQLiteHelper(db_fpath)
        self.selections_fpath = selections_fpath

        with open(self.selections_fpath) as fp:
            self.saved_selections = json.load(fp)

        main_box = toga.Box(style=Pack(direction=COLUMN))

        # Add label
        selected_recipes_label =  toga.Label(
            "Additional Items", 
            style=Pack(text_align=CENTER)
        )
        main_box.add(selected_recipes_label)

        # Add additional items
        self.additional_items = self.get_additional_items_box(
            self.saved_selections["additional_items"]
        )
        main_box.add(self.additional_items)

        # Add recipe selection box
        self.selection = self.get_recipe_selection_box()
        main_box.add(self.selection)

        # Add label
        selected_recipes_label =  toga.Label(
            "Selected Recipes", 
            style=Pack(text_align=CENTER)
        )
        main_box.add(selected_recipes_label)

        # Add selected recipes table box
        self.selected_table = self.get_selected_table_box(
            self.saved_selections["selected_recipes"]
        )
        main_box.add(self.selected_table)

        # Add populate cart button box
        self.populate_cart = self.get_populate_cart_button_box()
        main_box.add(self.populate_cart)

        # Add label
        selected_recipes_label =  toga.Label(
            "Shopping Cart", 
            style=Pack(text_align=CENTER)
        )
        main_box.add(selected_recipes_label)


        # Add shopping cart table box
        self.shopping_cart_table = self.get_shopping_cart_box()
        main_box.add(self.shopping_cart_table)

        # Add save button box
        self.save_button = self.get_save_button_box()
        main_box.add(self.save_button)

        # Add load button box
        self.load_button = self.get_load_button_box()
        main_box.add(self.load_button)

        # Define main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box

        self.main_window.show()

    def get_recipe_selection_box(self):

        selection_box = toga.Selection(
            items=self.get_recipe_list(),
            accessor="name",
            on_change=self.add_recipe_to_table,
            style=Pack(
                padding=5
            )
        )

        return selection_box
    
    def get_recipe_list(self) -> list:

        return sorted([x[0] for x in self.db_helper.get_recipes()])

    def get_selected_table_box(self, selected_recipes=[]):

        selected_table_box = toga.Table(
            headings=["Recipe Name"],
            data = selected_recipes,
            on_activate=self.remove_recipe,
            style=Pack(
                padding=5,
                height=100
            )
        )

        return selected_table_box

    def add_recipe_to_table(self, widget):

        self.selected_table.data.append((self.selection.value.name))

    def remove_recipe(self, widget, row):

        self.selected_table.data.remove(row)
        self.shopping_cart_table.data.clear()

    def get_populate_cart_button_box(self):
        
        button_box = toga.Button(
            "Populate Cart",
            on_press=self.populate_cart,
            style=Pack(
                padding=5
            )
        )

        return button_box
    
    def populate_cart(self, widget):

        self.shopping_cart_table.data.clear()
        data = self.get_ingredients()

        if data:
        
            for ingredient in data:
                
                self.shopping_cart_table.data.append(
                    (            
                        ingredient["ingredient"],
                        ingredient["quantity"]
                    )
                )

    def get_shopping_cart_box(self):

        shopping_cart_box = toga.Table(
            headings=["Ingredient", "Quantity"],
            data=[],
            on_activate=self.remove_ingredient,
            style=Pack(
                padding=5,
                height=200
            )
        )

        return shopping_cart_box
    
    def remove_ingredient(self, widget, row):

        self.shopping_cart_table.data.remove(row)

    def get_additional_items_box(self, value):

        additional_items_box = toga.MultilineTextInput(
            value=value,
            style=Pack(
                padding=5,
                height=100
            )
        )

        return additional_items_box
    

    def remove_additional_items(self, widget, row):

        pass     

    def get_save_button_box(self):

        button_box = toga.Button(
            "Save",
            
            on_press=self.save_selections,
            style=Pack(
                padding=5
            )
        )

        return button_box 
    
    def save_selections(self, widget):

        data = {
            "selected_recipes": [row.recipe_name for row in self.selected_table.data],
            "additional_items": self.additional_items.value
        }


        with open(self.selections_fpath, "w") as fp:
            json.dump(data, fp, indent=2)

        self.main_window.info_dialog(
            "Saved",
            "Selections saved"
        )

    def get_load_button_box(self):

        button_box = toga.Button(
            "Load",
            on_press=self.load_selections,
            style=Pack(
                padding=5
            )
        )

        return button_box 

    def load_selections(self, widget):

        with open(self.selections_fpath) as fp:
            data = json.load(fp)

        self.selected_table.data = data["selected_recipes"]
        self.additional_items.value = data["additional_items"]

        # Debugging
        # self.main_window.info_dialog(
        #     "Info",
        #     str(data["selected_recipes"]) + " " + self.additional_items.value
        # )

    def get_ingredients(self) -> list:

        ingredients = []

        if not hasattr(self.selected_table, "data") or not self.selected_table.data:
            return
        
        for row in self.selected_table.data:
            ingredients.append(
                self.db_helper.get_recipe_ingredients(row.recipe_name)
            )
        ingredients = flatten(ingredients)

        ingredient_to_unit = {}
        for ingredient in ingredients:
            if ingredient["name"] not in ingredient_to_unit and ingredient["unit"]:
                ingredient_to_unit[ingredient["name"]] = [ingredient["unit"]]
            elif ingredient["unit"]:
                ingredient_to_unit[ingredient["name"]].append(ingredient["unit"])
        for name in ingredient_to_unit.keys():
            ingredient_to_unit[name] = most_common(ingredient_to_unit[name])

        ingredient_to_quantity = {}
        ingredient_to_count = {}
        for ingredient in ingredients:
            if ingredient["name"] not in ingredient_to_quantity and ingredient["unit"]:
                ingredient_to_quantity[ingredient["name"]] = ingredient["quantity"] * self.units[ingredient["unit"]]
            elif ingredient["unit"]:
                ingredient_to_quantity[ingredient["name"]] += ingredient["quantity"] * self.units[ingredient["unit"]]

        for ingredient in ingredients:
            if ingredient["name"] not in ingredient_to_count and not ingredient["unit"]:
                ingredient_to_count[ingredient["name"]] = ingredient["quantity"]
            elif not ingredient["unit"]:
                ingredient_to_count[ingredient["name"]] += ingredient["quantity"]

        ingredient_to_all = {**ingredient_to_quantity, **ingredient_to_count}

        data = []

        for k, _ in ingredient_to_all.items():
            
            try:
                q = ingredient_to_quantity[k]
            except KeyError:
                pass

            try:
                c = ingredient_to_count[k]
            except KeyError:
                pass

            if k not in ingredient_to_count and k in ingredient_to_quantity:
                data.append({
                    "ingredient": k, 
                    "quantity": "%.2f %s" % (q.m_as(ingredient_to_unit[k]), ingredient_to_unit[k])
                })
            elif k in ingredient_to_count and k not in ingredient_to_quantity:
                data.append({
                    "ingredient": k, 
                    "quantity": "%d items" % (c)
                })
            elif k in ingredient_to_count and k in ingredient_to_quantity:
                data.append({
                    "ingredient": k, 
                    "quantity": "%.2f %s and %d items" % (q.m_as(ingredient_to_unit[k]), ingredient_to_unit[k], c)
                })
                

        return data


def main():
    return RecipeApp()

