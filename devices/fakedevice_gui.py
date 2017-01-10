import Tkinter as tk
from collections import defaultdict

import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from mpl_toolkits import mplot3d
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt


class ManipulatorView(object):
    instances = 0

    def __init__(self, tip_position, direction, stage, name=None):
        # offset is the actual position at the start
        # "position" is what a device would use (internal coordinates)
        self.offset = np.array(tip_position)
        self.position = np.zeros(3)
        self.stage = stage
        self.direction_x = np.array(direction)
        self.direction_x /= np.sqrt(np.sum(self.direction_x**2))
        self.direction_z = np.array([0, 0, 1])
        self.direction_y = np.cross(self.direction_x, self.direction_z)
        self.direction_y /= np.sqrt(np.sum(self.direction_y ** 2))
        ManipulatorView.instances += 1
        if name is None:
            name = 'Manipulator_%d' % ManipulatorView.instances
        self.name = name
        self.line_plot = {}
        self.dot_plot = {}

    def plot(self, axis):
        # plot the "pipette"
        x, y, z = self.position
        tip = self.offset + self.stage.position + x*self.direction_x + y*self.direction_y + z*self.direction_z
        start = tip - 50*1e3*self.direction_x
        if axis not in self.line_plot:
            self.line_plot[axis] = axis.plot3D([start[0], tip[0]], [start[1], tip[1]], [start[2], tip[2]])[0]
            # dot at its start
            self.dot_plot[axis] = axis.plot3D([start[0]], [start[1]], [start[2]], 'o')[0]
        else:
            self.line_plot[axis].set_data([start[0], tip[0]], [start[1], tip[1]])
            self.line_plot[axis].set_3d_properties([start[2], tip[2]])
            self.dot_plot[axis].set_data([start[0]], [start[1]])
            self.dot_plot[axis].set_3d_properties([start[2]])


class StageView(object):
    def __init__(self, outer_radius, inner_radius, position=(0, 0, 0), name=None):
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
        self.position = np.array(position)
        if name is None:
            name = 'Stage'
        self.name = name
        self.outer_circle = {}
        self.inner_circle = {}

    def plot(self, axis):
        from matplotlib.patches import Circle
        from mpl_toolkits.mplot3d.art3d import pathpatch_2d_to_3d
        if axis in self.outer_circle:
            self.outer_circle[axis].remove()
            self.inner_circle[axis].remove()
        self.outer_circle[axis] = outer_circle = Circle(self.position[:2], radius=self.outer_radius, edgecolor='gray', facecolor='none')
        self.inner_circle[axis] = inner_circle = Circle(self.position[:2], radius=self.inner_radius, color='red')
        axis.add_patch(outer_circle)
        axis.add_patch(inner_circle)
        pathpatch_2d_to_3d(outer_circle, z=self.position[2], zdir='z')
        pathpatch_2d_to_3d(inner_circle, z=self.position[2], zdir='z')


class CameraView(object):
    def __init__(self, lens_position, radius, height, name=None):
        self.position = lens_position
        self.radius = radius
        self.height = height
        if name is None:
            name = 'Camera'
        self.name = name
        self.lower_circle = {}
        self.upper_circle = {}

    def plot(self, axis):
        from matplotlib.patches import Circle
        from mpl_toolkits.mplot3d.art3d import pathpatch_2d_to_3d

        if axis not in self.lower_circle:
            self.lower_circle[axis] = lower_circle = Circle(self.position[:2], radius=self.radius,
                                                            edgecolor='gray', facecolor='none')
            self.upper_circle[axis] = upper_circle = Circle(self.position[:2], radius=self.radius,
                                                            edgecolor='gray', facecolor='none')
            axis.add_patch(lower_circle)
            axis.add_patch(upper_circle)
            pathpatch_2d_to_3d(lower_circle, z=self.position[2], zdir='z')
            pathpatch_2d_to_3d(upper_circle, z=self.position[2] + self.height, zdir='z')
            angles = np.linspace(0, 2*np.pi, 8)
            X = (self.position[0] + self.radius * np.cos(angles)).repeat(2).reshape((8, 2))
            Y = (self.position[1] + self.radius * np.sin(angles)).repeat(2).reshape((8, 2))
            Z = np.tile(np.array([self.position[2] + self.height, self.position[2]]), (8, 1))
            for x, y, z in zip(X, Y, Z):
                axis.plot3D(x, y, z, '-', color='gray')
        else:
            pass  # the camera doesn't move...


class SetupView(tk.Frame):
    def plot(self):
        for unit in self.units:
            unit.plot(self.axis_free)
            unit.plot(self.axis_fixed)
        self.canvas.draw()

    def __init__(self, parent, units, *args, **kwds):
        tk.Frame.__init__(self, parent, *args, **kwds)
        self.grid(row=0, column=0, sticky='nsew')
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        self.fig = plt.Figure(figsize=(10,5), dpi=100)
        self.units = units
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.axis_free = self.fig.add_subplot(121, projection='3d')
        self.axis_free.mouse_init()
        self.axis_fixed = self.fig.add_subplot(122, projection='3d')
        self.plot()
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.axis_free.grid('off')
        self.axis_free.set_axis_off()
        self.axis_free.set_aspect('equal')

        self.axis_fixed.grid('off')
        self.axis_fixed.set_axis_off()
        self.axis_fixed.set_aspect('equal')
        self.axis_free.set_xlim(-200 * 1e3, 200 * 1e3)
        self.axis_free.set_ylim(-200 * 1e3, 200 * 1e3)
        self.axis_free.set_zlim(0, 200 * 1e3)
        self.axis_fixed.set_xlim(-150 * 1e3, 150 * 1e3)
        self.axis_fixed.set_ylim(-150 * 1e3, 150 * 1e3)
        self.axis_fixed.set_zlim(0, 200 * 1e3)
        self.axis_free.set_title('Free view')
        self.axis_fixed.set_title('Top view')
        self.axis_fixed.disable_mouse_rotation()
        self.axis_free.view_init(elev=0, azim=90)
        self.axis_fixed.view_init(elev=90, azim=90)
        self.axis_free.dist = 8
        self.axis_fixed.dist = 7.5
        self.canvas.show()
        self.pack()


class Controller(tk.Frame):
    def __init__(self, parent, setup_view, units, *args, **kwds):
        tk.Frame.__init__(self, parent, *args, **kwds)
        self.setup_view = setup_view
        self.position_entries = defaultdict(list)
        self.units = units
        for unit in units:
            frame = tk.Frame(self)
            tk.Label(frame, text=unit.name).pack(side=tk.TOP)
            for axis_idx, axis_label in enumerate(['x', 'y', 'z']):
                axis = tk.Frame(frame)
                tk.Label(axis, text=axis_label).pack(side=tk.LEFT)
                tk.Button(axis, text='-', command=self.create_command(unit, axis_idx, '-')).pack(side=tk.LEFT)
                self.position_entries[unit.name].append(tk.Entry(axis))
                self.position_entries[unit.name][-1]['state'] = 'readonly'
                self.position_entries[unit.name][-1].pack(side=tk.LEFT)
                tk.Button(axis, text='+', command=self.create_command(unit, axis_idx, '+')).pack(side=tk.LEFT)
                axis.pack(side=tk.TOP)
            frame.pack(side=tk.LEFT)
        self.display_positions()
        self.pack()

    def create_command(self, unit, axis, change):
        return lambda: self.change_position(unit, axis, change)

    def change_position(self, unit, axis, change):
        if change == '-':
            changeby = -1e4
        else:
            changeby = 1e4
        unit.position[axis] = np.clip(unit.position[axis] + changeby, -100*1e3, np.inf)
        self.display_positions()
        self.setup_view.plot()

    def display_positions(self):
        for unit in self.units:
            entries = self.position_entries[unit.name]
            for axis_index, entry in enumerate(entries):
                entry['state'] = 'normal'
                entry.delete(0, tk.END)
                entry.insert(0, '%.1f' % unit.position[axis_index])
                entry['state'] = 'readonly'


class Master(object):

    def __init__(self, root, view, controls, comm_pipe):
        self.root = root
        self.view = view
        self.controls = controls
        self.comm_pipe = comm_pipe

    def communicate(self):
        if self.comm_pipe.poll():
            message = self.comm_pipe.recv()
            if message[0] == 'get':
                unit = message[1] // 3
                axis = message[1] % 3
                self.comm_pipe.send(self.view.units[unit].position[axis])
            elif message[0] == 'set':
                unit = message[1] // 3
                axis = message[1] % 3
                self.view.units[unit].position[axis] = message[2]
                self.root.after_idle(self.controls.display_positions)
                self.root.after_idle(self.view.plot)
            else:
                raise ValueError('Do not understand message: %s' % message)
        self.root.after(10, self.communicate)

# TODO: Add positions after calibration
# TODO: Add IPC with FakeDevice


def launch_device_gui(comm_pipe):
    root = tk.Tk()
    stage = StageView(150 * 1e3, 30 * 1e3)
    manipulator_1 = ManipulatorView([-150 * 1e3, 0, 150 * 1e3],
                                    [1, 0, -np.sin(45 / 180. * np.pi)], stage)
    manipulator_2 = ManipulatorView([150 * 1e3, 0, 150 * 1e3],
                                    [-1, 0, -np.sin(45 / 180. * np.pi)], stage)
    camera = CameraView([0, 0, 50 * 1e3], 20 * 1e3, 100 * 1e3)
    view = SetupView(root, [manipulator_1, manipulator_2, stage, camera])
    controls = Controller(root, view, [manipulator_1, manipulator_2, stage])
    master = Master(root, view, controls, comm_pipe)
    master.communicate()
    root.mainloop()
