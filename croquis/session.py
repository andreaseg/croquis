import time
from tkinter import *
from PIL import Image, ImageTk, ImageOps
from typing import Callable, Iterable

from croquis.constants import *
from croquis.util import *
from croquis.model import *
from croquis.monochrome import apply_monochrome
from croquis.i18n import translate


class SessionApp:
    NOT_SET = -1

    def __init__(
        self,
        tk: Tk,
        canvas: Canvas,
        title: str,
        geometry: tuple[int, int],
        monochrome: bool = False,
        locations: Iterable[str] = (),
        manual: bool = False,
        keybindings: dict[str, str] | None = None,
        on_exclude_image: Callable[[str], None] | None = None,
        zen_mode: bool = False,
        language: str = "en",
    ):
        self.tk = tk
        self.timer = SessionApp.NOT_SET
        self.is_paused = False
        self.is_manual = manual
        self.has_ended = False
        self.monochrome = monochrome
        self.locations = list(locations)
        self.on_exclude_image = on_exclude_image or (lambda path: None)
        self.zen_mode = zen_mode
        self.language = language
        self._zen_reveal_until: float = 0.0
        self._zen_reveal_after_id: str | None = None
        self._tick_after_id: str | None = None
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
        self.menu_button_widget: int | None = None
        self.resume_button_widget: int | None = None
        self.exclude_button_widget: int | None = None
        self.extend_timer_button_widget: int | None = None
        self.quit_button_widget: int | None = None
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

        keybindings = keybindings or DEFAULT_KEYBINDINGS
        tk.bind(f"<{keybindings['menu']}>", lambda _e: self.toggle_menu())
        tk.bind("<space>", lambda _e: self.toggle_menu())
        # Always (re)bind prev/next, even outside manual mode - a previous
        # SessionApp on this same tk root may have bound these (bind()
        # replaces per-sequence, it doesn't clear sequences a new session
        # doesn't rebind), so skipping the bind here would leave a stale
        # handler live. prev()/next() themselves no-op outside manual mode.
        tk.bind(f"<{keybindings['prev']}>", lambda _e: self.prev())
        tk.bind(f"<{keybindings['next']}>", lambda _e: self.next())
        tk.bind("<ButtonRelease-1>", self.left_click)
        tk.bind("<Configure>", lambda e: self.configure(e))

    def tick(self):
        if self.has_ended:
            # Defends against a tick that was already queued via tk.after()
            # firing after delete_children() tore this session down (its
            # after() handle is cancelled there too, but this guard is a
            # second line of defense against the exact class of bug that
            # was - see git history: an uncancelled tick() firing after
            # teardown called go_to_image()/load_image(), which created a
            # brand-new, untracked image widget on the shared canvas that
            # the next session had no way of knowing about or cleaning up).
            return

        if not self.is_paused:
            self.timer = max(self.timer - 1, SessionApp.NOT_SET)

        if self.timer == SessionApp.NOT_SET:
            self.go_to_image(self.index + 1)

        self.update_timer_text()
        self._apply_zen_visibility()

        if not self.has_ended:
            self._tick_after_id = self.tk.after(1000, self.tick)

    def update_timer_text(self):
        if (
            self.timer == SessionApp.NOT_SET
            or self.index >= len(self.imageset)
            or self.is_manual
        ):
            updated_text = ""
        else:
            updated_text = translate("{n}s", self.language, n=self.timer)

        self.canvas.itemconfigure(self.timer_widget, text=updated_text)
        self.canvas.itemconfigure(self.timer_widget_shadow, text=updated_text)

    def zen_reveal(self):
        """Briefly force the path/progress/timer overlay visible. Called on a
        real image change, on unpause, and on extend_timer - no-op outside
        Zen mode."""
        if not self.zen_mode:
            return
        self._zen_reveal_until = time.monotonic() + ZEN_REVEAL_SECONDS
        self._apply_zen_visibility()
        if self._zen_reveal_after_id is not None:
            self.tk.after_cancel(self._zen_reveal_after_id)
        self._zen_reveal_after_id = self.tk.after(
            ZEN_REVEAL_SECONDS * 1000, self._apply_zen_visibility
        )

    def _zen_final_countdown_active(self) -> bool:
        if (
            self.is_manual
            or self.index >= len(self.imageset)
            or self.timer == SessionApp.NOT_SET
        ):
            return False
        max_time = self.imageset[self.index][1]
        return self.timer <= zen_reveal_threshold(max_time)

    def _apply_zen_visibility(self):
        if not self.zen_mode or self.has_ended:
            return
        visible = (
            time.monotonic() < self._zen_reveal_until
            or self._zen_final_countdown_active()
        )
        state = NORMAL if visible else HIDDEN
        for widget in (
            self.path_widget,
            self.path_widget_shadow,
            self.progress_widget,
            self.progress_widget_shadow,
            self.timer_widget,
            self.timer_widget_shadow,
        ):
            self.canvas.itemconfigure(widget, state=state)

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
        self.canvas.coords(
            self.pause_text_widget, width / 2, height / 2 + MENU_TITLE_Y_OFFSET
        )
        self.reposition_menu_buttons()

    def reposition_menu_buttons(self):
        # Only the buttons actually shown by open_menu() get a slot, in
        # display order - so a mode without Extend Timer (manual sessions)
        # doesn't leave a gap where that button would've been.
        buttons = [self.resume_button_widget, self.exclude_button_widget]
        if not self.is_manual:
            buttons.append(self.extend_timer_button_widget)
        buttons.append(self.quit_button_widget)

        for i, widget in enumerate(buttons):
            self.canvas.coords(
                widget,
                self.width / 2,
                self.height / 2 + MENU_BUTTON_Y_OFFSET + i * MENU_BUTTON_SPACING,
            )

    def go_to_image(self, new_index: int) -> bool:
        if new_index < 0:
            return False
        previous_index = self.index
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

        if new_index != previous_index:
            self.timer = time
            self.zen_reveal()

        display_path = shorten_to_location(path, self.locations)
        display_text = (
            f"{display_path} {translate('(mirrored)', self.language)}"
            if is_mirrored
            else display_path
        )
        self.canvas.itemconfigure(self.path_widget, text=display_text)
        self.canvas.itemconfigure(self.path_widget_shadow, text=display_text)
        progress_text = f"{self.index + 1}/{len(self.imageset)}"
        self.canvas.itemconfigure(self.progress_widget, text=progress_text)
        self.canvas.itemconfigure(self.progress_widget_shadow, text=progress_text)
        self.canvas.itemconfigure(self.end_of_sequence_text_widget, state=HIDDEN)
        self.canvas.itemconfigure(self.restart_widget, state=HIDDEN)
        self.load_image(path, is_mirrored)

        return True

    def toggle_menu(self):
        if self.index >= len(self.imageset):
            return  # session already ended, nothing to pause/menu for
        if self.is_paused:
            self.close_menu()
        else:
            self.open_menu()

    def open_menu(self):
        print("OPEN MENU")
        self.is_paused = True
        self.canvas.itemconfigure(self.pause_background_widget, state=NORMAL)
        self.canvas.itemconfigure(self.pause_text_widget, state=NORMAL)
        self.canvas.itemconfigure(self.resume_button_widget, state=NORMAL)
        self.canvas.itemconfigure(self.exclude_button_widget, state=NORMAL)
        self.canvas.itemconfigure(self.quit_button_widget, state=NORMAL)
        self.canvas.itemconfigure(self.menu_button_widget, state=HIDDEN)
        self.canvas.itemconfigure(self.prev_widget, state=HIDDEN)
        self.canvas.itemconfigure(self.next_widget, state=HIDDEN)
        if not self.is_manual:
            self.canvas.itemconfigure(self.extend_timer_button_widget, state=NORMAL)

    def close_menu(self):
        print("CLOSE MENU")
        self.is_paused = False
        self.canvas.itemconfigure(self.pause_background_widget, state=HIDDEN)
        self.canvas.itemconfigure(self.pause_text_widget, state=HIDDEN)
        self.canvas.itemconfigure(self.resume_button_widget, state=HIDDEN)
        self.canvas.itemconfigure(self.exclude_button_widget, state=HIDDEN)
        self.canvas.itemconfigure(self.quit_button_widget, state=HIDDEN)
        self.canvas.itemconfigure(self.extend_timer_button_widget, state=HIDDEN)
        self.canvas.itemconfigure(
            self.menu_button_widget, state=HIDDEN if self.zen_mode else NORMAL
        )
        if self.is_manual:
            self.canvas.itemconfigure(self.prev_widget, state=NORMAL)
            self.canvas.itemconfigure(self.next_widget, state=NORMAL)
        self.zen_reveal()

    def exclude_current_image(self):
        path, _, _ = self.imageset[self.index]
        print("EXCLUDE", path)
        self.on_exclude_image(path)
        self.close_menu()
        self.go_to_image(self.index + 1)

    def extend_timer(self):
        print("EXTEND TIMER")
        self.timer += EXTEND_TIMER_SECONDS
        self.update_timer_text()
        self.zen_reveal()

    def quit_session(self):
        self.restart()

    def next(self):
        if not self.is_manual:
            return
        print("NEXT")
        went_to_new_image = self.go_to_image(self.index + 1)

        if went_to_new_image:
            self.timer += 1
            self.update_timer_text()

    def prev(self):
        if not self.is_manual:
            return
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
            if self.monochrome:
                img = apply_monochrome(img)
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
        if self._zen_reveal_after_id is not None:
            self.tk.after_cancel(self._zen_reveal_after_id)
            self._zen_reveal_after_id = None
        if self._tick_after_id is not None:
            self.tk.after_cancel(self._tick_after_id)
            self._tick_after_id = None
        self.canvas.delete(self.path_widget)
        self.canvas.delete(self.path_widget_shadow)
        self.canvas.delete(self.progress_widget)
        self.canvas.delete(self.progress_widget_shadow)
        self.canvas.delete(self.timer_widget)
        self.canvas.delete(self.timer_widget_shadow)
        self.canvas.delete(self.image_widget)
        self.canvas.delete(self.menu_button_widget)
        self.canvas.delete(self.resume_button_widget)
        self.canvas.delete(self.exclude_button_widget)
        self.canvas.delete(self.extend_timer_button_widget)
        self.canvas.delete(self.quit_button_widget)
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
    locations: Iterable[str] = (),
    monochrome: bool = False,
    excluded: Iterable[str] = (),
    keybindings: dict[str, str] | None = None,
    on_exclude_image: Callable[[str], None] | None = None,
    zen_mode: bool = False,
    language: str = "en",
):
    if mode.manual:
        manual_timer_placeholder = int(1)
        available_images = images_in_path(imageset.paths, locations, excluded)
        if not available_images:
            raise Exception("No images found for the selected image set(s).")
        image_paths = [
            (path, manual_timer_placeholder, False) for path in available_images
        ]
        random.shuffle(image_paths)
        print(f"Generated croquis plan of {len(image_paths)} images")
    else:
        image_paths = generate_random_image_sequence(
            imageset.paths, mode.timers, locations, excluded
        )
        print("Generated croquis plan:")
        for image_path, image_timer, is_flipped in image_paths:
            print(
                f" - '{image_path}'{' (mirrored)' if is_flipped else ''} for {image_timer}s"
            )

    app = SessionApp(
        tk,
        canvas,
        f"Croquis: {name}",
        dimensions,
        monochrome,
        locations,
        mode.manual,
        keybindings,
        on_exclude_image,
        zen_mode,
        language,
    )
    app.imageset = image_paths
    app.main_menu_callback = callback

    width, height = dimensions

    app.end_of_sequence_text_widget = canvas.create_text(
        width / 2,
        height / 2 - 60,
        text=translate("[END OF SESSION]", language),
        font=PAUSE_FONT,
        fill=PAUSE_TEXT_COLOR,
        anchor="center",
        state=HIDDEN,
    )
    btn = Button(
        tk,
        text=translate("Back to menu", language),
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
        height / 2 + MENU_TITLE_Y_OFFSET,
        text=translate("[PAUSED]", language),
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

    # ⏪⏩☰
    prev_next_state = NORMAL if mode.manual else HIDDEN

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
        state=prev_next_state,
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
        state=prev_next_state,
    )

    btn = Button(
        tk,
        text=MENU_BUTTON_TEXT,
        command=app.toggle_menu,
        width=BUTTON_WIDTH,
        height=BUTTON_HEIGHT,
        relief=FLAT,
        font=BUTTON_FONT,
        background=BUTTON_BACKGROUND_COLOR,
        foreground=BUTTON_TEXT_COLOR,
    )
    menu_button_state = HIDDEN if zen_mode else NORMAL
    app.menu_button_widget = canvas.create_window(
        BUTTON_EDGE_OFFSET,
        BUTTON_EDGE_OFFSET,
        anchor="nw",
        window=btn,
        state=menu_button_state,
    )

    def _menu_overlay_button(text: str, command) -> int:
        btn = Button(
            tk,
            text=text,
            command=command,
            width=20,
            height=2,
            relief=FLAT,
            font=("arial", 16),
            background=BUTTON_BACKGROUND_COLOR,
            foreground=BUTTON_TEXT_COLOR,
        )
        # Position is a placeholder - reposition_menu_buttons() (called
        # below) lays every menu button out based on which ones this mode
        # actually shows, so the initial y here doesn't matter.
        return canvas.create_window(
            width / 2,
            height / 2,
            anchor="center",
            window=btn,
            state=HIDDEN,
        )

    app.resume_button_widget = _menu_overlay_button(
        translate("Resume", language), app.close_menu
    )
    app.exclude_button_widget = _menu_overlay_button(
        translate("Skip / Exclude Image", language), app.exclude_current_image
    )
    app.extend_timer_button_widget = _menu_overlay_button(
        translate("Extend Timer (+{n}s)", language, n=EXTEND_TIMER_SECONDS),
        app.extend_timer,
    )
    app.quit_button_widget = _menu_overlay_button(
        translate("Quit to Menu", language), app.quit_session
    )
    app.reposition_menu_buttons()

    if mode.manual:
        app.go_to_image(app.index + 1)
    else:
        app.redraw(width, height)
        app.tick()
