import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import Label, get_url_hash, set_url_hash

from ..Model import init_vals, translate
from ._anvil_designer import MainTemplate
from .FiguresPanel import FiguresPanel

class Main(MainTemplate):
    label_xs_2100 = [55, 245, 410]
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run when the form opens.
        self.set_ambition_levers()
        self.pathways_dropdown.items = init_vals["example_pathways"].keys()

        self.set_event_handler("show", self.show)

    def show(self, **event_args):
        """`show` event handler. Last function to be called."""
        self.expert_label = Label(text="Start and End Year")
        self.expert_label.role = "subheading"
        self.expert_label.visible = False
        self.expert_toggle.text = "Switch to 2100 Mode"
        self.select_figures()
        input_values = self.get_url_vals()
        if (
            input_values["start_years"] != init_vals["default_start_years"]
            or input_values["end_years"] != init_vals["default_end_years"]
        ):
            self.set_expert_mode(True)
        self.update_graphs()

        self.title.text = translate("IESS 2047")
       
    def select_figures(self):
        """Initialise the FiguresPanel and add it to the plot area of the app."""
        self.figures_panel = FiguresPanel()
        self.plot_area.clear()
        self.plot_area.add_component(self.figures_panel)

    def update_graphs(self):
        """Collect the level values and update the graphs and url hash."""
        inputs = [
            (lever.value, lever.start_year, lever.end_year)
            for category in self.lever_group_panel.get_components()
            for group in category.group_panel.get_components()
            for lever in group.lever_panel.get_components()
        ]
        self.set_url(*zip(*inputs))
        self.figures_panel.calculate(*zip(*inputs), expert_mode=self.expert_mode)

    def get_url_vals(self):
        """Get lever values from url, if available. Otherwise use defaults."""
        url_hash = get_url_hash()
        try:
            inputs = list(map(int, url_hash["inputs"].split("-")))
            listing_start_years =  [2020] * len(inputs)
            listing_end_years =  [2047] * len(inputs)
            start_years = listing_start_years
            end_years = listing_end_years 

            if any(
                length != len(init_vals["default_inputs"])
                for length in (len(inputs), len(start_years), len(end_years))
            ):
                raise ValueError
            return dict(inputs=inputs, start_years=start_years, end_years=end_years)
        except (ValueError, KeyError, TypeError):
            self.set_defaults()
            return self.get_url_vals()

    def set_url(self, inputs=None, start_years=None, end_years=None):
        """Set lever values in the url.

        Args:
            inputs (list): A list of lever values
        """
        url_hash = get_url_hash()
        if inputs is None:
            inputs = url_hash["inputs"]
        else:
            inputs = "-".join(map(str, inputs))
        set_url_hash(dict(inputs=inputs))

    def set_defaults(self, years_only=False):
        """Set the url values (for levers and years) to their defaults.

        Args:
            years_only (bool): True when only changing the start and end year values and
                leaving the lever values. False also sets levers to defaults.
        """
        if years_only:
            self.set_url(
                start_years=init_vals["default_start_years"].copy(),
                end_years=init_vals["default_end_years"].copy(),
            )
        else:
            self.set_url(
                init_vals["default_inputs"].copy(),
                init_vals["default_start_years"].copy(),
                init_vals["default_end_years"].copy(),
            )

    def set_ambition_levers(self):
        """Set the values of the AmbitionLevers to match the urls.

        Updates the values if the LeverGroup is already populated, otherwise populates
        the LeverGroup.
        """
        input_values = self.get_url_vals()
        if self.lever_group_panel.items is None:
            items = []
            for category_title, group_names in init_vals["lever_categories"].items():
                groups = []
                for group_name in group_names:
                    levers = init_vals["lever_groups"][group_name]
                    groups.append(
                        {
                            "name": group_name,
                            "levers": levers,
                            "inputs": [
                                input_values["inputs"].pop(0)
                                for _ in range(len(levers["names"]))
                            ],
                            "start_years": [
                                input_values["start_years"].pop(0)
                                for _ in range(len(levers["names"]))
                            ],
                            "end_years": [
                                input_values["end_years"].pop(0)
                                for _ in range(len(levers["names"]))
                            ],
                        }
                    )
                items.append(
                    {
                        "category_title": category_title,
                        "groups": groups
                    }
                )
            self.lever_group_panel.items = items
        else:
            for category in self.lever_group_panel.get_components():
                for group in category.group_panel.get_components():
                    for lever in group.lever_panel.get_components():
                        lever.value = input_values["inputs"].pop(0)
                        lever.start_year = input_values["start_years"].pop(0)
                        lever.end_year = input_values["end_years"].pop(0)
                    group.lever_updated()

    def pathways_dropdown_change(self, **event_args):
        """This method is called when an item is selected from the dropdown"""
        self.pathways_dropdown.items = init_vals["example_pathways"].keys()
        self.set_defaults(years_only=True)
        if(event_args["sender"].selected_value != None):
            self.set_url(init_vals["example_pathways"][event_args["sender"].selected_value])
            self.set_ambition_levers()
            self.update_graphs()

    def custom_pathway(self, **event_args):
        self.pathways_dropdown.selected_value = None

    def reset_button_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.pathways_dropdown.items = init_vals["example_pathways"].keys() 
        self.pathways_dropdown.selected_value = self.pathways_dropdown.items[0]
        self.set_defaults()
        self.set_ambition_levers()
        self.update_graphs()


    @property
    def expert_mode(self):
        """A boolean property of the current app mode. True if in Expert Mode."""
        return self.expert_label in self.settings_title_card.get_components()

    def expert_toggle_click(self, **event_args):
        """This method is called when the `expert_toggle` button is clicked."""
        self.set_expert_mode(not self.expert_mode)
        self.update_graphs()

    def set_expert_mode(self, expert_mode):
        """Change app mode into Expert or back to Standard Mode.

        Expert Mode gives the option to select the start and end years for each Ambition
        Lever and extends the graphs into 2100. Standard Mode resets start and end year
        values to defaults and removes the ability to edit them and returns the year max
        to 2050.

        Args:
            expert_mode (bool): True when converting the app into Expert Mode.
        """
        if expert_mode:
            self.expert_toggle.text = "Go back to 2050 Mode"
            self.refresh_headers(self.label_xs_2100)
            self.settings_title_card.add_component(
                self.expert_label, x=self.label_xs_2100[2], y=0
            )
            self.main_area.role = "2100"
        else:
            self.expert_toggle.text = "Switch to 2100 Mode"
            self.expert_label.remove_from_parent()
            self.refresh_headers("")
            self.set_defaults(years_only=True)
            self.set_ambition_levers()
            self.main_area.role = "2050"

        if not expert_mode:
            # Reset lever_group_panel to return to original (non-expert) layout.
            # Removing the year selector element leaves an empty column so work
            # around completely by reinitialising the levers by nulling items
            # and setting again from url
            self.lever_group_panel.items = None
            self.set_ambition_levers()
        # else:
        #     for group in self.lever_group_panel.get_components():
        #         for lever in group.lever_group.get_components():
        #             lever.show_years()
        #         group.group_lever.show_years()
        #         group.group_lever.years.start_year.visible = False
        #         group.group_lever.years.end_year.visible = False

    def refresh_headers(self, xs):
        """Update x positions of labels acting as column headers"""
        col1_label, col2_label = self.settings_title_card.get_components()
        col1_label.remove_from_parent()
        col2_label.remove_from_parent()
        self.settings_title_card.add_component(col1_label, x=xs[0], y=0)
        self.settings_title_card.add_component(col2_label, x=xs[1], y=0)
