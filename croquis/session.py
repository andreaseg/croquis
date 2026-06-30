from tkinter import *
from PIL import Image, ImageTk, ImageOps
from typing import Callable

from croquis.constants import *
from croquis.util import *
from croquis.model import *


class SessionApp:
    NOT_SET = -1

    def __init__(self, tk: Tk, canvas: Canvas, title: str, geometry: tuple[int, int]):
        self.tk = tk
        self.timer = SessionApp.NOT_SET
        self.is_paused = False
        self.is_manual = False
        self.has_ended = False
        self.index = SessionApp.NOT_SET
        self.imageset: list[tuple[str, int, bool]] | None = None
        self.canvas: Canvas | None = canvas

        self.path_widget: int | None = None
        self.path_widget_shadow: int | None = None
        self.progress_widget: int | None = None
        self.progress_widget_shadow: int | None = None
        self.timer_widget: int | None = None
        self.timer_widget_shadow: int | None = None
        self.image_widget: int | None = None
        self.pause_widget: int | None = None
        self.play_widget: int | None = None
        self.prev_widget: int | None = None
        self.next_widget: int | None = None
        self.pause_background_widget: int | None = None
        self.pause_text_widget: int | None = None
        self.end_of_sequence_text_widget: int | None = None
        self.restart_widget: int | None = None

        self.main_menu_callback: Callable[[str], None] | None = None

        self.width, self.height = geometry
        if self.width < 256 or self.height < 256:
            print(f"WARNING!! tiny geometry {geometry}")  # TODO
        self.image_resize = False
        self.current_image = None

        tk.title(title)

        tk.bind("<space>", lambda _e: self.pause_or_play())
        tk.bind("<Left>", lambda _e: self.prev())
        tk.bind("<Right>", lambda _e: self.next())
        tk.bind("<ButtonRelease-1>", self.left_click)
        tk.bind("<Configure>", lambda e: self.configure(e))

    def tick(self):
        if not self.is_paused:
            self.timer = max(self.timer - 1, SessionApp.NOT_SET)

        if self.timer == SessionApp.NOT_SET:
            self.go_to_image(self.index + 1)

        self.update_timer_text()

        if not self.has_ended:
            self.tk.after(1000, self.tick)

    def update_timer_text(self):
        if self.index >= len(self.imageset):
            max_time = 999999999
        else:
            max_time = self.imageset[self.index][1]

        if (
            self.timer == SessionApp.NOT_SET
            or self.index >= len(self.imageset)
            or self.is_manual
        ):
            updated_text = ""
        elif self.timer > max_time:
            updated_text = f"{max_time}s"
        else:
            updated_text = f"{self.timer}s"

        self.canvas.itemconfigure(self.timer_widget, text=updated_text)
        self.canvas.itemconfigure(self.timer_widget_shadow, text=updated_text)

    def left_click(self, event):
        self.image_resize = event

    def configure(self, event):
        width = self.tk.winfo_width()
        height = self.tk.winfo_height()
        if (
            ((self.width, self.height) != (width, height))
            and width > 128
            and height > 128
        ):
            print(f"Resize to {width}x{height}")

            self.redraw(width, height)

    def redraw(self, width: int, height: int):
        self.width = width
        self.height = height
        self.go_to_image(self.index)

        self.canvas.coords(
            self.end_of_sequence_text_widget,
            width / 2,
            height / 2 - 60,
        )
        self.canvas.coords(self.restart_widget, width / 2, height / 2 + 80)
        self.canvas.coords(self.pause_background_widget, 0, 0, width, height)
        self.canvas.coords(
            self.pause_text_widget,
            width / 2,
            height / 2,
        )
        self.canvas.coords(
            self.path_widget_shadow,
            width - 12 + TEXT_SHADOW_OFFSET,
            height - 12 + TEXT_SHADOW_OFFSET,
        )
        self.canvas.coords(self.path_widget, width - 12, height - 12)
        self.canvas.coords(
            self.progress_widget_shadow,
            width - 12 + TEXT_SHADOW_OFFSET,
            12 + TEXT_SHADOW_OFFSET,
        )
        self.canvas.coords(
            self.progress_widget,
            width - 12,
            12,
        )
        self.canvas.coords(
            self.timer_widget_shadow,
            width / 2 + TEXT_SHADOW_OFFSET,
            12 + TEXT_SHADOW_OFFSET,
        )
        self.canvas.coords(self.timer_widget, width / 2, 12)
        self.canvas.coords(self.pause_widget, width / 2, height - BUTTON_EDGE_OFFSET)
        self.canvas.coords(self.play_widget, width / 2, height - BUTTON_EDGE_OFFSET)
        self.canvas.coords(
            self.prev_widget,
            width / 2 - BUTTON_POSITION_OFFSET,
            height - BUTTON_EDGE_OFFSET,
        )
        self.canvas.coords(
            self.next_widget,
            width / 2 + BUTTON_POSITION_OFFSET,
            height - BUTTON_EDGE_OFFSET,
        )

    def go_to_image(self, new_index: int) -> bool:
        if new_index < 0:
            return False
        self.index = min(max(SessionApp.NOT_SET, new_index), len(self.imageset))

        if new_index >= len(self.imageset):
            if self.image_widget:
                self.canvas.delete(self.image_widget)

            self.canvas.itemconfigure(self.timer_widget, text="")
            self.canvas.itemconfigure(self.timer_widget_shadow, text="")
            self.canvas.itemconfigure(self.progress_widget, text="")
            self.canvas.itemconfigure(self.progress_widget_shadow, text="")
            self.canvas.itemconfigure(self.path_widget, text="")
            self.canvas.itemconfigure(self.path_widget_shadow, text="")
            self.canvas.itemconfigure(self.end_of_sequence_text_widget, state=NORMAL)
            self.canvas.itemconfigure(self.restart_widget, state=NORMAL)
            self.timer = SessionApp.NOT_SET
            self.current_image = None
            return False

        path, time, is_mirrored = self.imageset[new_index]

        if new_index != self.timer:
            self.timer = time

        self.canvas.itemconfigure(
            self.path_widget, text=f"{path}{' (mirrored)' if is_mirrored else ''}"
        )
        self.canvas.itemconfigure(self.path_widget_shadow, text=path)
        progress_text = f"{self.index + 1}/{len(self.imageset)}"
        self.canvas.itemconfigure(self.progress_widget, text=progress_text)
        self.canvas.itemconfigure(self.progress_widget_shadow, text=progress_text)
        self.canvas.itemconfigure(self.end_of_sequence_text_widget, state=HIDDEN)
        self.canvas.itemconfigure(self.restart_widget, state=HIDDEN)
        self.load_image(path, is_mirrored)

        return True

    def pause_or_play(self):
        if self.is_paused:
            print("PLAY")
            self.canvas.itemconfigure(self.pause_widget, state=NORMAL)
            self.canvas.itemconfigure(self.play_widget, state=HIDDEN)
            self.canvas.itemconfigure(self.pause_background_widget, state=HIDDEN)
            self.canvas.itemconfigure(self.pause_text_widget, state=HIDDEN)
        else:
            print("PAUSE")
            self.canvas.itemconfigure(self.pause_widget, state=HIDDEN)
            self.canvas.itemconfigure(self.play_widget, state=NORMAL)
            self.canvas.itemconfigure(self.pause_background_widget, state=NORMAL)
            self.canvas.itemconfigure(self.pause_text_widget, state=NORMAL)

        self.is_paused = not self.is_paused

    def next(self):
        print("NEXT")
        went_to_new_image = self.go_to_image(self.index + 1)

        if went_to_new_image:
            self.timer += 1
            self.update_timer_text()

    def prev(self):
        print("PREV")
        went_to_new_image = self.go_to_image(self.index - 1)

        if went_to_new_image:
            self.timer += 1
            self.update_timer_text()

    def load_image(self, path: str, mirror: bool):
        redraw = False

        if self.current_image != path:
            self.current_image = path
            img = Image.open(path)
            if mirror:
                img = ImageOps.mirror(img)
            self._image_file = img
            print(f"Loaded image '{path}' with dimensions ({img.width},{img.height})")
            redraw = True
        else:
            img = self._image_file

        rescale = scale_rect_to_bounds(
            (img.width, img.height), (self.width, self.height)
        )
        mirror = -1 if mirror else 1
        scaled_image = (int(img.width * rescale), int(img.height * rescale))
        if (img.width, img.height) != scaled_image or redraw:
            print(f"Rescaling image to {scaled_image}")
            img = img.resize(scaled_image, Image.Resampling.LANCZOS)
            bg = ImageTk.PhotoImage(img)
            self._image_handle = bg
            redraw = True

        if redraw:
            print("Drawing image")
            if self.image_widget:
                print("Deleting image")
                self.canvas.delete(self.image_widget)

            self.image_widget = self.canvas.create_image(
                (self.width - img.width) / 2,
                (self.height - img.height) / 2,
                image=self._image_handle,
                anchor="nw",
            )
        self.canvas.tag_lower(self.image_widget)

    def delete_children(self):
        self.canvas.delete(self.path_widget)
        self.canvas.delete(self.path_widget_shadow)
        self.canvas.delete(self.progress_widget)
        self.canvas.delete(self.progress_widget_shadow)
        self.canvas.delete(self.timer_widget)
        self.canvas.delete(self.timer_widget_shadow)
        self.canvas.delete(self.image_widget)
        self.canvas.delete(self.pause_widget)
        self.canvas.delete(self.play_widget)
        self.canvas.delete(self.prev_widget)
        self.canvas.delete(self.next_widget)
        self.canvas.delete(self.pause_background_widget)
        self.canvas.delete(self.pause_text_widget)
        self.canvas.delete(self.end_of_sequence_text_widget)
        self.canvas.delete(self.restart_widget)
        self.has_ended = True

    def restart(self):
        self.delete_children()
        self.main_menu_callback("main_menu")


def start_session(
    tk: Tk,
    canvas: Canvas,
    name: str,
    imageset: ImageSet,
    mode: Mode,
    dimensions: tuple[int, int],
    callback: Callable[[str], None],
):
    if mode.manual:
        manual_timer_placeholder = int(1)
        image_paths = list(
            map(
                lambda path: (path, manual_timer_placeholder, False),
                images_in_path(imageset.paths),
            )
        )
        random.shuffle(image_paths)
        print(f"Generated croquis plan of {len(image_paths)} images")
    else:
        image_paths = generate_random_image_sequence(imageset.paths, mode.timers)
        print("Generated croquis plan:")
        for image_path, image_timer, is_flipped in image_paths:
            print(
                f" - '{image_path}'{' (mirrored)' if is_flipped else ''} for {image_timer}s"
            )

    app = SessionApp(tk, canvas, f"Croquis: {name}", dimensions)
    app.imageset = image_paths
    app.main_menu_callback = callback

    width, height = dimensions

    app.end_of_sequence_text_widget = canvas.create_text(
        width / 2,
        height / 2 - 60,
        text="[END OF SESSION]",
        font=PAUSE_FONT,
        fill=PAUSE_TEXT_COLOR,
        anchor="center",
        state=HIDDEN,
    )
    btn = Button(
        tk,
        text="Back to menu",
        command=app.restart,
        width=16,
        height=2,
        relief=FLAT,
        font=("arial", 20),
        background=BUTTON_BACKGROUND_COLOR,
        foreground=BUTTON_TEXT_COLOR,
    )
    app.restart_widget = canvas.create_window(
        width / 2, height / 2 + 80, anchor="s", window=btn, state=HIDDEN
    )

    app.pause_background_widget = canvas.create_rectangle(
        0, 0, width, height, state=HIDDEN, fill=PAUSE_BACKGROUND_COLOR
    )

    app.pause_text_widget = canvas.create_text(
        width / 2,
        height / 2,
        text="[PAUSED]",
        font=PAUSE_FONT,
        fill=PAUSE_TEXT_COLOR,
        anchor="center",
        state=HIDDEN,
    )

    app.path_widget_shadow = canvas.create_text(
        width - 12 + TEXT_SHADOW_OFFSET,
        height - 12 + TEXT_SHADOW_OFFSET,
        font=PATH_FONT,
        fill=TEXT_SHADOW_COLOR,
        anchor="se",
    )
    app.path_widget = canvas.create_text(
        width - 12,
        height - 12,
        font=PATH_FONT,
        fill=PATH_TEXT_COLOR,
        anchor="se",
    )
    app.progress_widget_shadow = canvas.create_text(
        width - 12 + TEXT_SHADOW_OFFSET,
        12 + TEXT_SHADOW_OFFSET,
        font=PROGRESS_FONT,
        fill=TEXT_SHADOW_COLOR,
        anchor="ne",
    )
    app.progress_widget = canvas.create_text(
        width - 12,
        12,
        font=PROGRESS_FONT,
        fill=PROGRESS_TEXT_COLOR,
        anchor="ne",
    )
    app.timer_widget_shadow = canvas.create_text(
        width / 2 + TEXT_SHADOW_OFFSET,
        12 + TEXT_SHADOW_OFFSET,
        font=TIMER_FONT,
        fill=TEXT_SHADOW_COLOR,
        anchor="n",
    )
    app.timer_widget = canvas.create_text(
        width / 2, 12, font=TIMER_FONT, fill=TIMER_TEXT_COLOR, anchor="n"
    )

    # ▶⏸⏯
    btn = Button(
        tk,
        text="⏸",
        command=app.pause_or_play,
        width=BUTTON_WIDTH,
        height=BUTTON_HEIGHT,
        relief=FLAT,
        font=BUTTON_FONT,
        background=BUTTON_BACKGROUND_COLOR,
        foreground=BUTTON_TEXT_COLOR,
    )
    app.pause_widget = canvas.create_window(
        width / 2, height - BUTTON_EDGE_OFFSET, anchor="s", window=btn
    )
    btn = Button(
        tk,
        text="▶",
        command=app.pause_or_play,
        width=BUTTON_WIDTH,
        height=BUTTON_HEIGHT,
        relief=FLAT,
        font=BUTTON_FONT,
        background=BUTTON_BACKGROUND_COLOR,
        foreground=BUTTON_TEXT_COLOR,
    )
    app.play_widget = canvas.create_window(
        width / 2, height - BUTTON_EDGE_OFFSET, anchor="s", window=btn, state=HIDDEN
    )

    btn = Button(
        tk,
        text="⏪",
        command=app.prev,
        width=BUTTON_WIDTH,
        height=BUTTON_HEIGHT,
        relief=FLAT,
        font=BUTTON_FONT,
        background=BUTTON_BACKGROUND_COLOR,
        foreground=BUTTON_TEXT_COLOR,
    )
    app.prev_widget = canvas.create_window(
        width / 2 - BUTTON_POSITION_OFFSET,
        height - BUTTON_EDGE_OFFSET,
        anchor="s",
        window=btn,
    )
    btn = Button(
        tk,
        text="⏩",
        command=app.next,
        width=BUTTON_WIDTH,
        height=BUTTON_HEIGHT,
        relief=FLAT,
        font=BUTTON_FONT,
        background=BUTTON_BACKGROUND_COLOR,
        foreground=BUTTON_TEXT_COLOR,
    )
    app.next_widget = canvas.create_window(
        width / 2 + BUTTON_POSITION_OFFSET,
        height - BUTTON_EDGE_OFFSET,
        anchor="s",
        window=btn,
    )

    if mode.manual:
        app.is_manual = True
        app.go_to_image(app.index + 1)
    else:
        app.redraw(width, height)
        app.tick()
