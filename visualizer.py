import sys
import argparse
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
import re
import ast
import numpy as np

# Function to extract data from log files
def extract_data_from_log(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    data = []
    for line in lines:
        matches = re.findall(r'<(\d+),([^,]+),([^,]+),([^>]+)>', line)
        if matches:
            data += list(matches)

    return data

# Function to generate data from log data and ABAC authorizations
def generate_data(log_data, authorizations):
    operations = {}
    users = set()
    resources = set()
    operation_counts = {}  # Track the number of occurrences of each operation

    for entry in log_data:
        _, user, resource, operation = entry
        users.add(user)
        resources.add(resource)
        auth_operations = authorizations.get((user, resource), set())
        auth_operations.add(operation)  # Include operation based on authorization

        # Count the occurrences of each operation
        if (user, resource, operation) in operation_counts:
            operation_counts[(user, resource, operation)] += 1
        else:
            operation_counts[(user, resource, operation)] = 1

        operations[(user, resource)] = auth_operations

    return list(users), list(resources), operations, operation_counts

# Map operations to colors using a colormap
def map_operations_to_colors(operations):
    unique_operations = list(set(operations))
    num_unique_operations = len(unique_operations)
    colormap = plt.get_cmap("tab20")
    operation_colors = {
        operation: colormap(i % num_unique_operations)
        for i, operation in enumerate(unique_operations)
    }
    return operation_colors

# PyQt5 Application for visualizing data
class App(QWidget):
    def __init__(self, graph, users, resources, authorizations, operation_colors, operation_counts):
        super().__init__()
        self.canvas = None
        self.switch_button = None
        self.resource_combo = None
        self.resource_label = None
        self.user_combo = None
        self.user_label = None
        self.user_color = "#AEC6CF"
        self.resource_color = '#FFD700'
        self.users = users
        self.resources = resources
        self.G = graph
        self.authorizations = authorizations
        self.operation_colors = operation_colors
        self.operation_counts = operation_counts  # Store the operation counts
        self.show_users = True  # Initialize to show user view
        self.init_ui()
        self.update_ui()

    def init_ui(self):
        self.setWindowTitle("Log Viewer")
        self.setGeometry(100, 100, 800, 600)

        # Create layouts
        main_layout = QVBoxLayout()
        user_layout = QHBoxLayout()
        resource_layout = QHBoxLayout()
        switch_layout = QHBoxLayout()

        # User selection
        self.user_label = QLabel("User:")
        self.user_combo = QComboBox()
        self.user_combo.addItems(self.users)
        user_layout.addWidget(self.user_label)
        user_layout.addWidget(self.user_combo)

        # Resource selection
        self.resource_label = QLabel("Resource:")
        self.resource_combo = QComboBox()
        self.resource_combo.addItems(self.resources)
        resource_layout.addWidget(self.resource_label)
        resource_layout.addWidget(self.resource_combo)

        # Switch button
        self.switch_button = QPushButton("Switch to Resources" if self.show_users else "Switch to Users")
        switch_layout.addWidget(self.switch_button)

        # Add layouts to the main layout
        main_layout.addLayout(user_layout)
        main_layout.addLayout(resource_layout)
        main_layout.addLayout(switch_layout)

        # Create a canvas for graph visualization
        self.canvas = FigureCanvas(plt.figure())
        main_layout.addWidget(self.canvas)

        # Connect signals to slots
        self.user_combo.currentIndexChanged.connect(self.update_ui)
        self.resource_combo.currentIndexChanged.connect(self.update_ui)
        self.switch_button.clicked.connect(self.toggle_view)

        # Set the main layout
        self.setLayout(main_layout)

    def toggle_view(self):
        self.show_users = not self.show_users
        self.switch_button.setText("Switch to Resources" if self.show_users else "Switch to Users")
        self.update_ui()

    def update_ui(self):
        selected_user = self.user_combo.currentText()
        selected_resource = self.resource_combo.currentText()

        self.user_label.setVisible(self.show_users)
        self.user_combo.setVisible(self.show_users)
        self.resource_label.setVisible(not self.show_users)
        self.resource_combo.setVisible(not self.show_users)

        # Clear the previous graph and draw the new subgraph with operations
        plt.clf()

        subgraph = nx.DiGraph()  # Initialize an empty subgraph

        if self.show_users:
            if selected_user:
                if selected_user in self.G:
                    # Create a subgraph showing all resources connected to the selected user
                    subgraph.add_node(selected_user, color=self.user_color)
                    for resource in self.G.successors(selected_user):
                        operation = self.G[selected_user][resource]["operation"]
                        subgraph.add_node(resource, color=self.resource_color)
                        subgraph.add_edge(selected_user, resource, operation=operation)
        else:
            if selected_resource:
                if selected_resource in self.G:
                    # Create a subgraph showing all users connected to the selected resource
                    subgraph.add_node(selected_resource, color=self.resource_color)
                    for user in self.G.predecessors(selected_resource):
                        operation = self.G[user][selected_resource]["operation"]
                        subgraph.add_node(user, color=self.user_color)
                        subgraph.add_edge(user, selected_resource, operation=operation)

        pos = nx.spring_layout(subgraph)
        colors = [subgraph.nodes[node].get("color", self.user_color) for node in subgraph.nodes()]

        # Add labels to edges (links) with the number of occurrences
        edge_labels = {}
        for u, v, data in subgraph.edges(data=True):
            operation = data.get("operation", "").split(",")
            operation = [operation.strip() for operation in operation]
            l=""
            for i in operation:
                occurrences = self.operation_counts.get((u, v, i), 0)
                l+=f"{i}({occurrences}),"
            l = l[:-1]
            edge_labels[(u, v)] = l

        # Draw nodes and edges
        nx.draw(subgraph, pos, with_labels=True, node_color=colors, font_color="black",
                node_size=1000, font_size=10, font_weight="bold", width=2)

        nx.draw_networkx_edge_labels(subgraph, pos, edge_labels=edge_labels, font_color='red')

        plt.title("ABAC Log Visualization")

        # Draw the graph on the canvas
        self.canvas.draw()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="ABAC Log Visualizer")
    parser.add_argument("-a","--auth_file", type=str, help="Path to the log data file")
    parser.add_argument("-l", "--log_file", nargs='+', type=str, help="Paths to authorization data files")
    args = parser.parse_args()
    # Extract data from log files
    log_data = []
    for file_path in args.log_file:
        log_data += extract_data_from_log(file_path)

    with open(args.auth_file, 'r') as file:
        # the first line is a list of usernames
        users = file.readline().strip()[1:-1].split(',')
        users = [user.strip()[1:-1] for user in users]
        # the second line is a list of resources
        resources = file.readline().strip()[1:-1].split(',')
        resources = [resource.strip()[1:-1] for resource in resources]
        # the third line is a dictionary of the form {(uid,rid):{operations}} it's corresponding of the authorization user/resource/operation
        data = ast.literal_eval(file.readline().strip())

        # Verify if the parsed data is a dictionary
        if isinstance(data, dict):
            authorizations = data
        else:
            print("Error: Invalid authorization data")
            exit(1)

        # Generate data for visualization, including operation counts
        _, _, operations, operation_counts = generate_data(log_data, authorizations)
        # Create a directed graph
        G = nx.DiGraph()
        for (user, resource), auth_operations in operations.items():
            G.add_edge(user, resource, operation=", ".join(auth_operations))

        # Map operations to colors using a colormap
        operation_colors = map_operations_to_colors(set(operation for auth_operations in operations.values() for operation in auth_operations))

        # Create the PyQt5 application
        app = QApplication(sys.argv)
        window = App(G, users, resources, authorizations, operation_colors, operation_counts)
        window.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
