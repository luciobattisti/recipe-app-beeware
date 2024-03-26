from SQLiteHelper import SQLiteHelper

helper = SQLiteHelper('../recipe.db')


class Test:
    def test_get_ingredient_id(self):
        ingredient_name = 'almond'
        ingredient_id = helper.get_ingredient_id(ingredient_name)

        assert(ingredient_id == 11)

    def test_add_recipe(self):
        recipe_name = "classic pasta"
        ingredients = [{"name": "penne", "quantity": 1, "unit": "lb"},
                       {"name": "sauce", "quantity": 1, "unit": "lb"},
                       {"name": "aubergine", "quantity": 9, "unit": "oz"},
                       {"name": "courgette", "quantity": 9, "unit": "oz"},
                       {"name": "onion", "quantity": 4, "unit": "oz"}]
        helper.add_recipe(recipe_name, ingredients)
        delete_success = helper.delete_recipe(recipe_name)
        add_success = helper.add_recipe(recipe_name, ingredients)

        assert((add_success, delete_success) == (True, True))

    def test_get_recipes(self):
        recipes = helper.get_recipes()
        print("recipes = {}".format(recipes))

        assert(recipes is not None)

    def test_get_ingredients(self):
        recipe_name = "classic pasta"
        ingredients = helper.get_recipe_ingredients(recipe_name)
        expected_ingredients = [{"name": "penne", "quantity": 1, "unit": "lb"},
                       {"name": "sauce", "quantity": 1, "unit": "lb"},
                       {"name": "aubergine", "quantity": 9, "unit": "oz"},
                       {"name": "courgette", "quantity": 9, "unit": "oz"},
                       {"name": "onion", "quantity": 4, "unit": "oz"}]

        assert(ingredients == expected_ingredients)






