import sys
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
import re


def extract_data_from_log(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    data = []
    for line in lines:
        matches = re.findall(r'<(\d+),([^,]+),([^,]+),([^>]+)>', line)
        if matches:
            data += list(matches)

    return data


def generate_data(data_):
    operations_ = {}
    users_ = set()
    resources_ = set()

    for i in data_:
        t = (i[1], i[2])
        users_.add(i[1])
        resources_.add(i[2])
        if t in operations_:
            operations_[t].add(i[3])
        else:
            operations_[t] = {i[3]}
    return list(users_), list(resources_), operations_


class App(QWidget):
    def __init__(self, graph, users_, resources_):
        super().__init__()
        self.canvas = None
        self.switch_button = None
        self.resource_combo = None
        self.resource_label = None
        self.user_combo = None
        self.user_label = None
        self.user_color = "#AEC6CF"
        self.resource_color = '#FFD700'
        self.users = users_
        self.resources = resources_
        self.G = graph
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

        node_colors = [subgraph.nodes[n].get("color", 'skyblue') for n in subgraph.nodes]
        labels = {(u, v): d["operation"] for u, v, d in subgraph.edges(data=True)}
        nx.draw(subgraph, pos, with_labels=True, node_size=500, node_color=node_colors, font_size=10,
                font_color='black')
        nx.draw_networkx_edge_labels(subgraph, pos, edge_labels=labels)
        self.canvas.draw()


if __name__ == '__main__':

    log_file = ["data.log"]  # set all log file path

    data = []
    for i in log_file:
        data += extract_data_from_log(i)
    users, resources, operations = generate_data(data)
    G = nx.DiGraph()
    # print(operations)
    for k, o in operations.items():
        G.add_edge(k[0], k[1], operation=o)

    app = QApplication(sys.argv)
    ex = App(G, users, resources)
    ex.show()
    sys.exit(app.exec_())
