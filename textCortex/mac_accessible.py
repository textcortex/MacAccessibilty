from ApplicationServices import *
from a11y.utils import (get_frontmost,
                        get_app_ref,
                        set_app_changed_notification,
                        setNotification,
                        get_attribute_value,
                        get_parametrized_attribute_value,
                        is_attribute_settable, stop_event_loop,
                        set_attribute_value
                        )
from ApplicationServices import AXObserverCreate, kAXLayoutChangedNotification
import objc
from CoreFoundation import CFRange
from ApplicationServices import AXValueCreate, kAXValueCFRangeType

editable = ['AXTextArea', 'AXTextField', 'AXWebArea']

# TODO : Imprve event names
'''
    selected_text = triggred when text selected
    app_changed = triggred when active app changed
    alt_enter_pressed = triggred when 'Alt+Enter' pressed
    focus_ui_change = triggred when focused ui changed
    ui_reized = triggred when ui position chaned or resized
'''


class MacAccessbility:
    def __init__(self, callback):
        self.callback = callback
        self.frontmost_app = get_frontmost()
        self.process_id = self.frontmost_app.processIdentifier()
        self.selected_text = ""
        self.focused_elemnt = get_attribute_value(
            get_app_ref(self.process_id), 'AXFocusedUIElement')

    def native_text_field_selected_text(self):
        element = self.focused_elemnt
        selected_text = get_attribute_value(element, 'AXSelectedText')
        is_editable = is_attribute_settable(element, 'AXSelectedText')
        location, lenght = get_attribute_value(element, 'AXSelectedTextRange')
        self.selected_text = selected_text
        my_nsrange = CFRange(location, lenght)
        my_axvalue = AXValueCreate(kAXValueCFRangeType, my_nsrange)

        possition, size = get_parametrized_attribute_value(
            element, 'AXBoundsForRange', my_axvalue)
        x = possition.x
        y = possition.y

        width = size.width
        height = size.height
        dict = {'selected_text': selected_text, 'is_editable': is_editable, 'position': {
            'x': x, 'y': y}, 'size': {'width': width, 'height': height}}
        return dict

    def selected_text_change(self):
        @objc.callbackFor(AXObserverCreate)
        def selected_text_change_observer_callback(observer, element, notification, refcon):
            selected_text = get_attribute_value(element, 'AXSelectedText')
            role = get_attribute_value(element, 'AXRole')
            self.focused_elemnt = element
            dict = {}

            if selected_text:
                if role in ['AXTextField', 'AXTextArea']:
                    dict = self.native_text_field_selected_text()
                else:
                    dict = {'response': 'not implemted yet '}

            self.callback('text_select', dict)

        return selected_text_change_observer_callback

    def set_text_relative_to_inseration_point(self, value, direction):
        location, _ = get_attribute_value(
            self.focused_elemnt, 'AXSelectedTextRange')
        if direction == 'above':
            # AXReplaceRangeWithText
            my_nsrange = CFRange(0, location)
            my_axvalue = AXValueCreate(kAXValueCFRangeType, my_nsrange)
            set_attribute_value(self.focused_elemnt,
                                'AXSelectedTextRange', my_axvalue)
            self.set_selected_text(value)
        elif direction == 'below':
            my_nsrange = CFRange(location, location+1)
            my_axvalue = AXValueCreate(kAXValueCFRangeType, my_nsrange)
            set_attribute_value(self.focused_elemnt,
                                'AXSelectedTextRange', my_axvalue)
            self.set_selected_text(value)
        else:
            return 'please use above or below'

    def get_text_above_inseration_point(self):
        location, _ = get_attribute_value(
            self.focused_elemnt, 'AXSelectedTextRange')
        my_nsrange = CFRange(0, location)
        my_axvalue = AXValueCreate(kAXValueCFRangeType, my_nsrange)
        text = get_parametrized_attribute_value(
            self.focused_elemnt, 'AXStringForRange', my_axvalue)
        return text

    def set_selected_text(self, value):
        set_attribute_value(self.focused_elemnt, 'AXSelectedText', value)

    def ui_focused_change(self):
        @objc.callbackFor(AXObserverCreate)
        def focused_ui_chaned_observer_callback(observer, element, notification, refcon):
            role = get_attribute_value(element, 'AXRole')
            self.focused_elemnt = element
            callback_argv = {'role': role}
            if role in editable:
                self.callback('focus_ui_change', callback_argv)
                ref = get_app_ref(self.process_id)
                setNotification(
                    ref, self.process_id, 'AXSelectedTextChanged', self.selected_text_change())
        return focused_ui_chaned_observer_callback

    def ui_resized(self):
        @objc.callbackFor(AXObserverCreate)
        def focused_ui_resized(observer, element, notification, refcon):
            role = get_attribute_value(self.focused_elemnt, 'AXRole')
            if role in editable:
                selected_text = get_attribute_value(
                    self.focused_elemnt, 'AXSelectedText')
                dict = {}
                if selected_text:
                    if role in ['AXTextField', 'AXTextArea']:
                        dict = self.native_text_field_selected_text()
                    else:
                        dict = {'response': 'not implemted yet '}

                self.callback('ui_reized', dict)
        return focused_ui_resized

    def app_changed_event(self, notification):
        app = notification.userInfo()[
            'NSWorkspaceApplicationKey']
        # TODO: Change this to bundle identifier
        if app.localizedName() != 'textCortex':
            self.frontmost_app = app
            if self.frontmost_app.isFinishedLaunching():
                self.process_id = self.frontmost_app.processIdentifier()
                ref = get_app_ref(self.process_id)
                element = get_attribute_value(ref, 'AXFocusedUIElement')
                if element:
                    self.focused_elemnt = element
                    role = get_attribute_value(element, 'AXRole')
                    call_back_argv = {'role': role, 'name': self.frontmost_app.localizedName(
                    ), 'bundle_id': self.frontmost_app.bundleIdentifier()}
                    self.callback('app_changed', call_back_argv)

                    if role in editable:
                        setNotification(
                            ref, self.process_id, 'AXSelectedTextChanged', self.selected_text_change())
                        setNotification(
                            ref, self.process_id, 'AXWindowResized', self.ui_resized())
                        setNotification(ref, self.process_id,
                                        'AXWindowMoved', self.ui_resized())

                    setNotification(
                        ref, self.process_id, 'AXFocusedUIElementChanged', self.ui_focused_change())
                else:
                    call_back_argv = {'role': None, 'name': self.frontmost_app.localizedName(
                    ), 'bundle_id': self.frontmost_app.bundleIdentifier()}
                    self.callback('app_changed', call_back_argv)
                    setNotification(
                        ref, self.process_id, 'AXFocusedUIElementChanged', self.ui_focused_change())

                    setNotification(ref, self.process_id, '',
                                    self.selected_text_change())

    def key_pressed(self, event):
        # listen for 'Alt+Enter' Key
        if event.modifierFlags() & NSAlternateKeyMask and str(event.keyCode()) == "36":
            role = get_attribute_value(self.focused_elemnt, 'AXRole')
            if role in editable:
                location, _ = get_attribute_value(
                    self.focused_elemnt, 'AXSelectedTextRange')
                selected_text = self.get_text_above_inseration_point()
                if self.selected_text:
                    selected_text = self.selected_text
                    self.set_selected_text(self.selected_text)

                my_nsrange = CFRange(location, 1)
                my_axvalue = AXValueCreate(kAXValueCFRangeType, my_nsrange)
                possition, size = get_parametrized_attribute_value(
                    self.focused_elemnt, 'AXBoundsForRange', my_axvalue)

                x = possition.x
                y = possition.y

                width = size.width
                height = size.height
                dict = {'selected_text': selected_text, 'is_editable': True, 'position': {
                    'x': x, 'y': y}, 'size': {'width': width, 'height': height}}
                self.callback('alt_enter_pressed', dict)

    def start(self):
        set_app_changed_notification(self.app_changed_event, self.key_pressed)

    def stop(self):
        stop_event_loop()
