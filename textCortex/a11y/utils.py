from ApplicationServices import *
from CoreFoundation import *
from PyObjCTools import AppHelper, MachSignals
from AppKit import NSWorkspace,NSApplication
import signal
import objc
import Foundation
from .error import *
import re
observer_list = {}

def AxUIElemnt_To_Py_Object( attrValue):
    def list_helper(list_value):
        list_builder = []
        for item in list_value:
            list_builder.append(AxUIElemnt_To_Py_Object( item))
        return list_builder

    def number_helper(number_value):
        success, int_value = CFNumberGetValue(number_value, kCFNumberIntType, None)
        if success:
            return int(int_value)

        success, float_value = CFNumberGetValue(number_value, kCFNumberDoubleType, None)
        if success:
            return float(float_value)

        raise ErrorUnsupported('Error converting numeric attribute: {}'.format(number_value))

    def axuielement_helper(element_value):
        return element_value

    cf_attr_type = CFGetTypeID(attrValue)
    cf_type_mapping = {
        CFStringGetTypeID(): str,
        CFBooleanGetTypeID(): bool,
        CFArrayGetTypeID(): list_helper,
        CFNumberGetTypeID(): number_helper,
        AXUIElementGetTypeID(): axuielement_helper,
    }
    try:
        return cf_type_mapping[cf_attr_type](attrValue)
    except KeyError:
        # did not get a supported CF type. Move on to AX type
        pass

    ax_attr_type = AXValueGetType(attrValue)
    ax_type_map = {
        kAXValueCGSizeType: NSSizeFromString,
        kAXValueCGPointType: NSPointFromString,
        kAXValueCFRangeType: NSRangeFromString,
        kAXValueCGRectType:NSRectFromString,
    }
    try:
        extracted_str = re.search('{.*}', attrValue.description()).group()
        return tuple(ax_type_map[ax_attr_type](extracted_str))
    except KeyError:
        raise ErrorUnsupported('Return value not supported yet: {}'.format(ax_attr_type))

def sigHandler(ig):
    AppHelper.stopEventLoop()
    raise KeyboardInterrupt('Keyboard interrupted Run Loop')

def setError(error_code, error_message):
    error_mapping = {
        kAXErrorAttributeUnsupported: ErrorUnsupported, # -25205
        kAXErrorActionUnsupported: ErrorUnsupported, # -25206
        kAXErrorNotificationUnsupported: ErrorUnsupported, # -25207
        kAXErrorAPIDisabled: ErrorAPIDisabled, # -25211
        kAXErrorInvalidUIElement: ErrorInvalidUIElement, # -25202
        kAXErrorCannotComplete: ErrorCannotComplete, # -25204
        kAXErrorNotImplemented: ErrorNotImplemented, # -25208
    }
    msg = '{} (AX Error {})'.format(error_message, error_code)
    print(msg)
    raise error_mapping[error_code](msg)

def get_attributes(ref):
    err, attr = AXUIElementCopyAttributeNames(ref, None)

    if err != kAXErrorSuccess:
        setError(err, 'Error retrieving attribute list')
    else:
        return list(attr)
    
def get_attribute_value(ref, attr):
    err, attrValue = AXUIElementCopyAttributeValue(ref, attr, None)
    if err == kAXErrorNoValue:
        return
   
    if err != kAXErrorSuccess:
        if err == kAXErrorNotImplemented:
            setError(err, 'Attribute not implemented')
        else:
            setError(err, 'Error retrieving attribute')

    return AxUIElemnt_To_Py_Object( attrValue)

def get_parametrized_attribute_value(ref,attr,parameter):
    err, attrValue = AXUIElementCopyParameterizedAttributeValue(ref, attr, parameter,None)
    print(attrValue)
    if err == kAXErrorNoValue:
        return

    if err != kAXErrorSuccess:
        if err == kAXErrorNotImplemented:
            setError(err, 'Attribute not implemented')
        else:
            setError(err, 'Error retrieving attribute')

    return AxUIElemnt_To_Py_Object( attrValue)

def is_attribute_settable(ref,attr):
    err, settable = AXUIElementIsAttributeSettable(ref, attr, None)
    if err != kAXErrorSuccess:
        setError(err, 'Error querying attribute')
    return settable

def set_attribute_value(ref,attr,value):
    err, to_set = AXUIElementCopyAttributeValue(ref, attr, None)
    if err != kAXErrorSuccess:

        setError(err, 'Error retrieving attribute to set')
    is_settable = is_attribute_settable(ref,attr)
    if not is_settable:
        raise ErrorUnsupported('Attribute is not settable')

    err = AXUIElementSetAttributeValue(ref, attr, value)
    if err != kAXErrorSuccess:
        if err == kAXErrorIllegalArgument:
            setError(err, 'Invalid value for element attribute')
        setError(err, 'Error setting attribute value')

def get_frontmost():
    frontmost_app = NSWorkspace.sharedWorkspace().frontmostApplication()
    return frontmost_app

def get_app_ref(pid):
    app_ref = AXUIElementCreateApplication(pid)

    if app_ref is None:
        raise ErrorUnsupported('Error getting app ref')
    
    return app_ref

def start_event_loop():
    AppHelper.runEventLoop()

import ctypes
class MyRefcon(ctypes.Structure):
    _fields_ = [("data", ctypes.py_object)]

def setNotification(ref,pid,notificationStr,observerCallback):
    data ={'ref':ref,'pid':pid}
  
    err, observer = AXObserverCreate(pid, observerCallback, None)
    observer_list[notificationStr] = {'observer':observer,'ref':ref}
    
    refcon_obj = MyRefcon()
    refcon_obj.data = data

    err = AXObserverAddNotification(
            observer, 
            ref,
            notificationStr,
            pid
        )

    if err != kAXErrorSuccess:
            setError(err, 'Could not add notification to observer')

        #Add observer source to run loop
    CFRunLoopAddSource(
        CFRunLoopGetCurrent(),
        AXObserverGetRunLoopSource(observer),
        kCFRunLoopDefaultMode
    )
    


def set_app_changed_notification(call_back):
    workspace = NSWorkspace.sharedWorkspace()
    center = workspace.notificationCenter()
    center.addObserverForName_object_queue_usingBlock_(NSWorkspaceDidActivateApplicationNotification, None, None, call_back)
    center.addObserverForName_object_queue_usingBlock_(NSWorkspaceDidLaunchApplicationNotification, None, None, call_back)
        
   
    
    AppHelper.runConsoleEventLoop(
        mode=kCFRunLoopDefaultMode,
        installInterrupt=False,
        maxTimeout=10,
    )

def stop_event_loop():
    AppHelper.stopEventLoop()