"""
Application to turn recipes into a shopping list
"""
from datetime import datetime
import pint
import toga
import os
from collections import Counter
from recipeapp.db.sqlite_helper.SQLiteHelper import SQLiteHelper
from recipeapp.gdrive.GoogleDriveHelper import GoogleDriveHelper
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

# Utility section ################################################################

flatten = lambda l: [item for sublist in l for item in sublist]

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

        self.db_helper = SQLiteHelper(f"{self.paths.app}/resources/recipe.db")
        self.gdrive_folder = "recipe-app"

        main_box = toga.Box(style=Pack(direction=COLUMN))
        
        # Add recipe selection box
        self.selection = self.get_recipe_selection_box()
        main_box.add(self.selection)

        # Add selected recipes table box
        self.selected_table = self.get_selected_table_box()
        main_box.add(self.selected_table)

        # Add save shopping list button box
        self.save_button = self.get_save_button_box()
        main_box.add(self.save_button)

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

    def get_selected_table_box(self):

        selected_table_box = toga.Table(
            headings=["Recipe Name"],
            data=[],
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

    def get_save_button_box(self):

        button_box = toga.Button(
            "Save Shopping List",
            # icon=toga.Icon("resources/google_drive_icon.png"), 
            on_press=self.save_shopping_list,
            style=Pack(
                padding=5
            )
        )

        return button_box
    
    def save_shopping_list(self, widget):

        data = self.get_shopping_list()

        if data:
            file_name = "recipe-{}.csv".format(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
            file_path = f"{self.paths.app}/resources/{file_name}"
            
            with open(file_path, "w") as fp:
                fp.write(data)

            self.main_window.info_dialog(
                "Saving",
                'Saving "{}" to google drive folder "{}"'.format(
                    file_name, self.gdrive_folder    
                )
            )
            
            gdrive_hlp = GoogleDriveHelper(
                 f"{self.paths.app}/resources/credentials.json",
                 f"{self.paths.app}/resources/token.json",
            )
            
            folder_id = gdrive_hlp.get_or_create_folder(self.gdrive_folder)
            
            gdrive_hlp.upload_csv_to_google_drive(
                 file_path, 
                 folder_id
            )

            os.remove(file_path)

    def get_shopping_list(self) -> list:

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

        data = "Recipe Name,,,Additional Items \n"
        for row in self.selected_table.data:
            data += "%s,,, \n" % (row.recipe_name)        
        data += ",,,\n"

        data += "Ingredient,Quantity,,\n"
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
                data += "%s,%.2f %s\n" % (k, q.m_as(ingredient_to_unit[k]), ingredient_to_unit[k])
            elif k in ingredient_to_count and k not in ingredient_to_quantity:
                data += "%s,%d items\n" % (k, c)
            elif k in ingredient_to_count and k in ingredient_to_quantity:
                data += "%s,%.2f %s and %d items\n" % (k, q.m_as(ingredient_to_unit[k]), ingredient_to_unit[k], c)

        return data


def main():
    return RecipeApp()

