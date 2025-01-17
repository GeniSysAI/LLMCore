import xml.etree.ElementTree as ET
import json
import os

class AssistantDefinition:
    def __init__(self, xml_file_path, json_file_path):
        self.xml_file_path = xml_file_path
        self.json_file_path = json_file_path
        self.tree = None
        self.root = None

    def load_xml(self):
        """Load the XML file and parse it."""
        if not os.path.exists(self.xml_file_path):
            self.helpers.log_message("Error", "XML file not found: " + self.xml_file_path)
            raise FileNotFoundError(f"XML file not found: {self.xml_file_path}")
        self.tree = ET.parse(self.xml_file_path)
        self.root = self.tree.getroot()

    def load_json(self):
        """Load JSON data from the specified file."""
        if not os.path.exists(self.json_file_path):
            raise FileNotFoundError(f"JSON file not found: {self.json_file_path}")
        with open(self.json_file_path, 'r', encoding='utf-8') as json_file:
            self.json_data = json.load(json_file)

    def update_agent_definition(self):
        """Update the XML file's agent definition with values from the JSON data."""
        agent_name = self.json_data.get("name", "")
        role = self.json_data.get("role", "")

        # Locate the <Name> element under <Assistant>
        assistant_element = self.root.find(".//Name")

        if assistant_element is not None:
            assistant_element.text = agent_name
        else:
            raise ValueError("<Name> element not found in the XML file.")

        # Locate the <Role> element under <Assistant>
        role_element = self.root.find(".//Role")

        if role_element is not None:
            role_element.text = role
        else:
            raise ValueError("<Name> element not found in the XML file.")

    def get_updated_xml_string(self):
        """Return the updated XML as a string."""
        return ET.tostring(self.root, encoding='unicode', method='xml')

    def run_update(self):
        """Perform the full update process."""
        self.load_xml()
        self.load_json()
        self.update_agent_definition()
        return self.get_updated_xml_string()