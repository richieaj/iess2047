from ._anvil_designer import LeverCategoryTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

class LeverCategory(LeverCategoryTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)
        # title, group_names = self.item

        self.category_title.text = self.item["category_title"]
        self.group_panel.items = self.item["groups"]
