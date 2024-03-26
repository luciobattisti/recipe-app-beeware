__author__ = 'Alessandro Lusci'

import sqlite3


class SQLiteHelper:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)

    def get_ingredient_id(self, ingredient_name):
        cur = self.conn.cursor()

        query = """
        SELECT * FROM ingredient
        WHERE name = '{0}';
        """.format(ingredient_name)

        cur.execute(query)
        rows = cur.fetchall()

        if rows:
            return rows[0][0]

    def get_ingredient(self, id):
        cur = self.conn.cursor()

        query = """
         SELECT * FROM ingredient
         WHERE id = {0};
         """.format(id)

        cur.execute(query)
        rows = cur.fetchall()

        if rows:
            return rows[0][1]

    def get_all_ingredients(self):
        """
        Returns all ingredients from db.

        :returns:List of ingredients
        :rtype: ``list``
        """
        cur = self.conn.cursor()

        query = "SELECT * FROM ingredient"

        cur.execute(query)
        rows = cur.fetchall()

        return rows

    def get_recipe_id(self, recipe_name):
        cur = self.conn.cursor()

        recipe_name = recipe_name.replace("'", "''")

        query = """
        SELECT * FROM recipe
        WHERE name = '{0}';
        """.format(recipe_name)

        cur.execute(query)
        rows = cur.fetchall()

        if rows:
            return rows[0][0]

    def add_recipe(self, name, ingredient):
        cur = self.conn.cursor()

        # Add recipe
        query = """
        INSERT INTO recipe
        (name) VALUES ('{0}');
        """.format(name)
        try:
            cur.execute(query)
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(e)
            return False

        # Get recipe and ingredient ids
        recipe_id = self.get_recipe_id(name)

        # Add ingredients
        for elem in ingredient:
            ingredient_id = self.get_ingredient_id(elem["name"])
            query = """
            INSERT INTO recipe_ingredient
            (recipe, ingredient, quantity, unit) 
            VALUES ({0},{1},{2},'{3}');
            """.format(recipe_id, ingredient_id, elem['quantity'],
                       elem['unit'])
            try:
                cur.execute(query)
                self.conn.commit()
            except sqlite3.IntegrityError as e:
                print(e)
                return False

        return True

    def delete_recipe(self, name):
        cur = self.conn.cursor()
        recipe_id = self.get_recipe_id(name)

        # Delete ingredients
        query = """
                DELETE FROM recipe_ingredient
                WHERE recipe = {0};
                """.format(recipe_id)
        try:
            cur.execute(query)
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(e)
            return False

        # Delete recipe
        query = """
                DELETE FROM recipe
                WHERE name = '{0}';
                """.format(name)
        try:
            cur.execute(query)
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(e)
            return False

        return True

    def get_recipes(self):
        cur = self.conn.cursor()

        query = """
                SELECT name FROM recipe
                """
        cur.execute(query)
        rows = cur.fetchall()

        if rows:
            return rows

    def get_recipe_ingredients(self, name):
        cur = self.conn.cursor()
        recipe_id = self.get_recipe_id(name)

        query = """
                SELECT * FROM recipe_ingredient
                WHERE recipe = {0};
                """.format(recipe_id)

        cur.execute(query)
        rows = cur.fetchall()

        ingredients = []
        for row in rows:
            ingredients.append({"name": self.get_ingredient(row[1]),
                                "quantity": row[2],
                                "unit": row[3]})

        return ingredients
