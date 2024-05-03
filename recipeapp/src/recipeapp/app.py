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

        self.db_helper = SQLiteHelper(db_fpath)
        self.selections_fpath = selections_fpath

        with open(self.selections_fpath) as fp:
            self.saved_selections = json.load(fp)

        # Create Main Box
        main_box = self.create_main_box()

        # Menu 
        options = toga.Group("Menu")
        opt_add_recipe_box = toga.Command(
            self.show_add_recipe_box,
            text="Add/Delete Recipe",
            tooltip="Show Add Recipe Window",
            group=options,
        )

        opt_main_box = toga.Command(
            self.show_main_box,
            text="Main",
            tooltip="Show main box",
            group=options
        )
        
        self.commands.add(opt_add_recipe_box)
        self.commands.add(opt_main_box)
        
        # Define main window
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box

        self.main_window.show()

    def create_main_box(self) -> toga.Box:

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
        self.populate_cart_button = self.get_populate_cart_button_box()
        main_box.add(self.populate_cart_button)

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

        return main_box

    def show_add_recipe_box(self, widget):
        self.main_window.content.clear()

        self.ingredients_list = self.get_ingredient_list()

        add_recipe_box = toga.Box(style=Pack(direction=COLUMN))

        # Add Recipe Name label
        recipe_name_label =  toga.Label(
            "Recipe Name", 
            style=Pack(text_align=CENTER)
        )
        add_recipe_box.add(recipe_name_label)

        # Add Recipe Name input 
        self.recipe_name_input = toga.TextInput(
            style=Pack(
                padding=5
            )
        )
        add_recipe_box.add(self.recipe_name_input)

        # Add "Add Ingredient" label
        add_ingredient_label =  toga.Label(
            "Ingredients", 
            style=Pack(text_align=CENTER)
        )
        add_recipe_box.add(add_ingredient_label)

        # Add recipe ingredient table
        self.recipe_ingredient_table = self.get_recipe_ingredient_table()
        add_recipe_box.add(self.recipe_ingredient_table)

        # Add ingredient input 
        ingredient_input = toga.TextInput(
            placeholder="Refine Ingredient Search",
            style=Pack(
                padding=5
            ),
            on_change=self.update_ingredients_list
        )
        add_recipe_box.add(ingredient_input)

        # Add ingredient selection 
        self.ingredient_selection = self.get_ingredient_selection_box()
        add_recipe_box.add(self.ingredient_selection)

        # Add quantity box
        self.quantity_box = toga.NumberInput(
            style=Pack(
                padding=5
            ),
            min_value=1,
            value=1
        )

        add_recipe_box.add(self.quantity_box)

        # Add unit selection box
        self.unit_selection = toga.Selection(
            items=self.units.keys(),
            accessor="name",
            style=Pack(
                padding=5
            ),
        )

        add_recipe_box.add(self.unit_selection)

        # Include Add Ingredient button
        self.add_ingredient_button = self.get_add_ingredient_button()
        add_recipe_box.add(self.add_ingredient_button)

        # Include Add Recipe button
        save_recipe_button = self.get_save_recipe_button()
        add_recipe_box.add(save_recipe_button)

        # Include Delete Recipe button
        delete_recipe_button = self.get_delete_recipe_button()
        add_recipe_box.add(delete_recipe_button)

        self.main_window.content = add_recipe_box

    def show_main_box(self, widget):

        self.main_window.content.clear()
        
        main_box = self.create_main_box()
        self.main_window.content = main_box

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
                height=125
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
    
    def get_ingredient_selection_box(self):
        
        selection_box = toga.Selection(
            items=self.ingredients_list, # We may need to place this in a better place
            accessor="name",
            style=Pack(
                padding=5
            )
        )
        
        return selection_box

    def get_ingredient_list(self):

        ingredients = [x[1] for x in self.db_helper.get_all_ingredients()]

        return ingredients
    
    def update_ingredients_list(self, widget):

        search_str = widget.value.lower()

        curr_ingredients = [x for x in self.ingredients_list if search_str in x]

        self.ingredient_selection.items = curr_ingredients

    def get_recipe_ingredient_table(self, ingredients=[]):

            table_box = toga.Table(
                headings=["Name", "Quantity", "Unit"],
                data = ingredients,
                on_activate=self.remove_ingredient_from_recipe,
                style=Pack(
                    padding=5,
                    height=150
                )
            )

            return table_box
    
    def remove_ingredient_from_recipe(self, widget, row):

        self.recipe_ingredient_table.data.remove(row)
    
    def get_add_ingredient_button(self):
            
        button_box = toga.Button(
            "Add Ingredient",
            on_press=self.add_ingredient,
            style=Pack(
                padding=5
            )
        )

        return button_box

    def add_ingredient(self, widget):

        ingredient = (
            self.ingredient_selection.value.name,
            self.quantity_box.value,
            self.unit_selection.value.name            
        )

        self.recipe_ingredient_table.data.append(ingredient)

    def get_save_recipe_button(self):

        button_box = toga.Button(
            "Save Recipe",
            on_press=self.save_recipe,
            style=Pack(
                padding=5
            )
        )

        return button_box

    def save_recipe(self, widget):

        ingredients = []
        for item in self.recipe_ingredient_table.data:
            ingredients.append(
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit
                }
            )

        recipe_name = self.recipe_name_input.value
        if not recipe_name:
            self.main_window.info_dialog(
                "Invalid Recipe Name",
                "Please enter a valid recipe name",
            )
        
            return
        
        if not ingredients:
            self.main_window.info_dialog(
                "No Ingredients",
                "Please add at least 1 ingredient",
            )

            return

        success = self.db_helper.add_recipe(
                self.recipe_name_input.value.lower(), 
                ingredients
            )
        
        if success:
            self.main_window.info_dialog(
            "Success",
            f"Recipe {recipe_name} added successfully",
        )
        else:
            self.main_window.info_dialog(
                "Error",
                "Could not save recipe. Make sure that the name hasn't been already used"
            )

    def get_delete_recipe_button(self):

        button_box = toga.Button(
            "Delete Recipe",
            on_press=self.delete_recipe,
            style=Pack(
                padding=5
            )
        )

        return button_box

    def delete_recipe(self, widget):

        recipe_name = self.recipe_name_input.value.lower()
        if not recipe_name:
            self.main_window.info_dialog(
                "Invalid Recipe Name",
                "Please enter a valid recipe name",
            )

            return
        
        recipe_id = self.db_helper.get_recipe_id(recipe_name)

        if not recipe_id:
            self.main_window.info_dialog(
                "Error",
                f"Cannot find {recipe_name} in database",
            )

            return

        success = self.db_helper.delete_recipe(recipe_name)

        if success:
            self.main_window.info_dialog(
                "Success",
                f"Recipe {recipe_name} DELETED successfully",
            )
        else:
            self.main_window.info_dialog(
                "Error",
                "Could not delete recipe. Make sure that the recipe name exists"
            )

        
def main():
    return RecipeApp()

