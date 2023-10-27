import os
import time
import autoit
import keyboard
import mss
import numpy as np
import win32con
import win32gui
from PIL import Image, ImageDraw, ImageFont
from pynput.mouse import Controller, Button


# import pyautogui


class CrysalisManager:
    def __init__(self, text_browser):
        self.mouse = Controller()
        self.click_index = 0
        self.ewald = "Ewald Explorer (1.0.6)"
        self.shell = "Shell command window (Break/Pause - interrupts)"
        self.crys = "CrysAlisPro - RED"
        self.hwnd = 0
        self.current_group = 2
        self.um_i = True
        self.um_i_header = "UM i with threshold"
        self.last_um_i_hwnd = 0
        self.screen_idle = np.array([])
        self.last_state = np.array([])
        self.dt = 0.05
        self.action_delay = 1
        self.dt_long = 0.5
        self.timeout = 10
        self.msg = text_browser
        self.calibration = {"Crystal_tab_header": 0,
                            "Crystal_tab_lattice": 0,
                            "Crystal_tab_uc_finding": 0,
                            "Crystal_tab_lattice_improve_with_tolerance": 0,
                            "Crystal_tab_results_up_left_corner": 0,
                            "Crystal_tab_results_dw_right_corner": 0,
                            "Selection_tab_header": 0,
                            "Selection_tab_select_all_btn": 0,
                            "Selection_tab_move_selected_to_btn": 0,
                            "Selection_tab_groups": 0,
                            "Group_tab_#": 0,
                            "Group_tab_indexed": 0,
                            "Group_tab_wrong": 0,
                            "Group_tab_group1_checkbox": 0,
                            "Ewald_space_up_left_corner": 0,
                            "Ewald_space_dw_right_corner": 0
                            }

        # Ewald explorer coordinates
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0

        # Unit cell finding window
        self.x0_uc = 0
        self.y0_uc = 0
        self.x1_uc = 0
        self.y1_uc = 0

        # Output
        self.summary = {}
        self.out_width = 0
        self.out_height = 0
        self.break_height = 10

        # Layout parameters
        self.chbox_size_px = 10
        self.chbox_size_px = 10
        self.chbox_threshold = 255

    def is_window_open(self, window):
        win32gui.EnumWindows(self.open_callback, window)
        return self.hwnd

    def open_callback(self, hwnd, window):
        if win32gui.IsWindowVisible(hwnd):
            self.hwnd = win32gui.FindWindow(None, window)

    def improve_with_tolerance(self):
        self.click(self.calibration["Crystal_tab_lattice"], 1)
        self.click(self.calibration["Crystal_tab_lattice_improve_with_tolerance"], 1)
        hwnd = False
        while not hwnd:
            hwnd = self.is_window_open(self.um_i_header)
            time.sleep(self.dt)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(self.dt)
        keyboard.write("0.05", delay=self.dt)
        time.sleep(self.dt)
        keyboard.send("enter")
        time.sleep(self.dt)
        self.last_um_i_hwnd = hwnd
        self.wait_screen_changed()
        self.click(self.calibration["Group_tab_wrong"], 1)
        self.wait_screen_changed()

    def index_single(self, group_index):
        # chose the group of interest
        if not self.select_group_new(group_index):
            time.sleep(1)
            return False
        # Index
        self.indexing(group_index)
        # Apply Lattice improvement with tolerance
        if self.um_i:
            self.improve_with_tolerance()
        # Move indexed to specific group
        self.move_all_to_group(group_index)
        # Pick all
        self.click(self.calibration["Group_tab_wrong"], 1)
        self.wait_screen_changed()
        self.set_current_group(group_index)
        return True

    def indexing(self, group_index):
        self.click(self.calibration["Crystal_tab_header"], 1)
        self.click(self.calibration["Crystal_tab_lattice"], 1)
        self.click(self.calibration["Crystal_tab_uc_finding"], 1)
        if not self.x0_uc:
            self.finding_is_active()
        self.wait_screen_changed()
        self.click(self.calibration["Group_tab_wrong"], 1)
        self.wait_screen_changed()

    def multi_indexing(self):
        self.summary = {}
        ewald_hwnd = self.is_window_open(self.ewald)
        # Step 1. Check if Ewald explorer is open
        if not ewald_hwnd:
            self.msg.append_log_message("Ewald explorer is closed", err=True)
            return
        # Step 2. Put ewald explorer in front
        self.put_in_front(ewald_hwnd)
        self.calibrate()
        self.last_state = self.grab_screen()
        # Step 3. Actual indexing
        self.msg.append_log_message("-Start autoindexer-", service=True)
        for i in range(3, 5):
            self.msg.append_log_message("Indexing group: " + str(i), service=True)
            if self.index_single(i):
                self.summary[i] = self.grab_results()
            time.sleep(self.dt)
        self.create_output(self.summary)
        self.msg.append_log_message("-Autoindexing is done-", service=True)

    def create_output(self, summary):
        if not bool(summary):
            self.msg.append_log_message(message="The summary is empty", err=True)
            return False
        blank = Image.new(mode="RGBA", size=(self.out_width * 2, self.break_height), color=(160, 160, 160, 255))
        output = blank
        font_size = 20
        font = ImageFont.truetype('verabd-webfont.ttf', font_size)
        for key, indexed_params in summary.items():
            title = "Group " + str(key)
            group_title = Image.new(mode="RGBA", size=(self.out_width, self.out_height), color=(182, 182, 182, 255))
            draw = ImageDraw.Draw(group_title)
            draw.text((int(0.2 * self.out_width), int(0.5 * (self.out_height - font_size))), title, font=font,
                      fill="black")
            hor_layout = np.concatenate([group_title, indexed_params], axis=1)
            output = np.concatenate([output, hor_layout, blank], axis=0)
        pil_im = Image.fromarray(output)
        pil_im.show(title="Don't forget to close this window")

    def click(self, pos, n_clicks, speed=1):
        # debug
        basedir = "debug"
        basename = "click_" + str(self.click_index) + ".jpg"
        path = os.path.join(basedir, basename)
        img = self.screenshot(pos[1] - 25, pos[0] - 25, width=50, height=50)
        pil_im = Image.fromarray(img)
        pil_im = pil_im.convert("RGB")
        pil_im.save(path)
        self.click_index += 1

        # autoit.mouse_click("left", pos[0], pos[1], n_clicks, speed=self.action_delay)
        self.mouse.position = pos
        time.sleep(self.dt)
        self.mouse.click(button=Button.left)
        time.sleep(self.dt)

    def scroll(self, pos, n_scrolls, direction="up"):
        # mouse.move(str(pos[0]), str(pos[1]))
        # time.sleep(self.dt)
        # if direction == "up":
        #     mouse.wheel(delta=n_scrolls)
        # if direction == "down":
        #     mouse.wheel(delta=-n_scrolls)
        autoit.mouse_move(pos[0], pos[1], speed=self.action_delay)
        time.sleep(self.dt)
        autoit.mouse_wheel(direction, n_scrolls)
        time.sleep(self.dt)

    def is_clickable(self, x, y, width, height, threshold):
        img = self.screenshot(int(x), int(y), width, height)
        if img.mean() < threshold:
            self.msg.append_log_message("The current group is empty", err=True)
            return False
        return True

    @staticmethod
    def put_in_front(hwnd):
        win32gui.SetForegroundWindow(hwnd)
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

    def finding_is_active(self):
        finding_window = 0
        while not finding_window:
            finding_window = win32gui.FindWindow(None, "Data processing.")
            if finding_window:
                self.x0_uc, self.y0_uc, self.x1_uc, self.y1_uc = win32gui.GetWindowRect(finding_window)
                self.last_state = self.grab_screen()

    def set_current_group(self, group_index):
        self.current_group = group_index
        if self.current_group >= 14:
            self.current_group = 14

    def move_all_to_group(self, group_index):
        self.click(self.calibration["Selection_tab_header"], 1)
        self.scroll(pos=self.calibration["Selection_tab_groups"], n_scrolls=20, direction="up")
        self.scroll(pos=self.calibration["Selection_tab_groups"], n_scrolls=group_index - 1, direction="down")
        self.click(self.calibration["Selection_tab_select_all_btn"], 1)
        self.wait_screen_changed()
        self.click(self.calibration["Selection_tab_move_selected_to_btn"], 1)
        self.wait_screen_changed()

    def select_group_new(self, group_index):
        max_groups_in_layout = 6
        x0 = self.calibration["Group_tab_group1_checkbox"][0]
        y0 = self.calibration["Group_tab_group1_checkbox"][1]
        delta = 17
        self.click(self.calibration["Group_tab_#"], 1)
        if 2 < group_index <= 6:
            y = y0 + delta * (group_index - 1)
        elif 6 < group_index <= 12:
            self.scroll(self.calibration["Group_tab_group1_checkbox"], n_scrolls=2, direction="down")
            y = y0 + delta * (group_index - max_groups_in_layout - 1)
        elif 12 < group_index <= 18:
            self.scroll(self.calibration["Group_tab_group1_checkbox"], n_scrolls=4, direction="down")
            y = y0 + delta * (group_index - max_groups_in_layout * 2 - 1)
        elif 18 < group_index <= 20:
            self.scroll(self.calibration["Group_tab_group1_checkbox"], n_scrolls=5, direction="down")
            y = y0 + delta * (group_index - max_groups_in_layout * 3 + 3)
        if not self.is_clickable(y - 0.5 * self.chbox_size_px, x0 - 0.5 * self.chbox_size_px,
                                 width=self.chbox_size_px, height=self.chbox_size_px,
                                 threshold=self.chbox_threshold):
            return False
        self.click((x0, y), 1)
        self.wait_screen_changed()
        return True

    def calibrate(self):
        self.is_window_open(self.ewald)
        self.x0, self.y0, self.x1, self.y1 = win32gui.GetWindowRect(self.hwnd)
        self.out_width = (self.calibration["Crystal_tab_results_dw_right_corner"][0]
                          - self.calibration["Crystal_tab_results_up_left_corner"][0])
        self.out_height = (self.calibration["Crystal_tab_results_dw_right_corner"][1]
                           - self.calibration["Crystal_tab_results_up_left_corner"][1])
        self.screen_idle = self.grab_screen()

    def grab_screen(self):
        uc_margin = 30
        x0, y0 = self.calibration["Ewald_space_up_left_corner"]
        x1, y1 = self.calibration["Ewald_space_dw_right_corner"]
        width = x1 - x0
        height = y1 - y0

        img = self.screenshot(x0, y0, width, height)
        img[self.y0_uc - y0 - uc_margin: self.y1_uc - y0 + uc_margin,
        self.x0_uc - x0 - uc_margin: self.x1_uc - x0 + uc_margin] = 0

        return img

    def grab_results(self):
        self.click(self.calibration["Crystal_tab_header"], 2)
        x0, y0 = self.calibration["Crystal_tab_results_up_left_corner"]
        time.sleep(self.dt_long)
        img = self.screenshot(y0, x0, self.out_width, self.out_height)
        return img

    @staticmethod
    def screenshot(x0, y0, width, height):
        with mss.mss() as sct:
            monitor = {"top": x0, "left": y0, "width": width, "height": height}
            img = np.array(sct.grab(monitor))
        return img

    def wait_screen_changed(self):
        t_start = time.time()
        while True:
            if keyboard.is_pressed("ctrl") and keyboard.is_pressed("c"):
                self.msg.append_log_message("Early stop by user", service=True)
                self.create_output(self.summary)
                exit()
            time.sleep(self.dt)
            current_state = self.grab_screen()
            if np.sum(current_state - self.last_state) > 0:
                self.last_state = current_state
                return
            if time.time() - t_start > self.timeout:
                self.msg.append_log_message("Timeout, no screen changes was detected over the time limit of 10 seconds"
                                            " due to: One of the indexing actions exceed time limit or Something went "
                                            "wrong during the indexing procedure. Most probably you just moved a mouse,"
                                            " try to avoid it while autoindexing is running :)", err=True)
                exit()

    def manual_screen_calibration(self):
        ewald_hwnd = self.is_window_open(self.ewald)
        # Step 1. Check if Ewald explorer is open
        if not ewald_hwnd:
            self.msg.append_log_message("Ewald explorer is closed", err=True)
            return

        # Step 2. Put ewald explorer in front
        self.put_in_front(ewald_hwnd)

        # Calibration loop
        index = 1
        self.msg.append_log_message("Multiple steps procedure. At each step move your mouse cursor to the"
                                    "indicated position and press 'c' on your keyboard" + "\n", service=True)

        for key, value in self.calibration.items():
            self.msg.append_log_message("Step " + str(index) + ": " +
                                        "cursor position" + "'" + key + "'", service=True)
            while True:
                time.sleep(self.dt)
                key_event = keyboard.read_event()
                if key_event.event_type == "up" and key_event.name == "c":
                    self.calibration[key] = win32gui.GetCursorPos()
                    break
            index += 1
        self.msg.append_log_message("Calibration is done", service=True)


def main():
    cm = CrysalisManager(text_browser=None)
    print(cm.is_window_open(cm.ewald))
    cm.put_in_front(cm.is_window_open(cm.ewald))
    # cm.select_group_new(group_index=4)
    while True:
        key_event = keyboard.read_event()
        print(key_event.event_type, key_event.name)
        time.sleep(cm.dt)


if __name__ == "__main__":
    main()
