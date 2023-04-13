from kivy.app import App
from kivy.base import Builder
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition, FadeTransition,SwapTransition, NoTransition
from kivy.clock import Clock
from kivy.properties import ObjectProperty
import json
import os

from jnius import autoclass


#Important code for bluetooth is at line 212-268
#It is commented


class blankPage(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class welcomePage(Widget):
    
    okButton = ObjectProperty(None)

    def okPressed(self):
        controlApp.screen_manager.current='settingsPage'

class infoPage(Widget):
    def switchToControlPage(self, *event):
        controlApp.screen_manager.transition = SlideTransition(direction= 'up')
        controlApp.screen_manager.current = 'controlPage'
    def switchToSettingsPage(self, *event):
        controlApp.screen_manager.transition = SlideTransition(direction= 'up')
        controlApp.screen_manager.current = 'settingsPage'


class settingsPage(Widget):
    maxSpeedSlider = ObjectProperty(None)
    trimSlider = ObjectProperty(None)
    lightOn = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            with open(controlApp.settings_filename, 'r') as file_object:
                self.settings = json.load(file_object)
            self.maxSpeedSlider.value = self.settings[0]
            self.trimSlider.value = self.settings[2]
            self.lightOn.state = self.settings[3]
        except FileNotFoundError:
            pass

    def switchToControlPage(self, *clock):
        controlApp.screen_manager.transition = SwapTransition(duration= 0.7)
        controlApp.screen_manager.current = 'controlPage'

    def switchToInfoPage(self, *event):
        controlApp.screen_manager.transition = SlideTransition(direction= 'down')
        controlApp.screen_manager.current = 'infoPage'
        self.saveData()

    def saveButtonPressed(self):
        self.saveData()        
        Clock.schedule_once(self.switchToControlPage, 0.5)
    
    def resetTrim(self):
        self.trimSlider.value = 0

    def saveData(self, *clock):
        self.settings = [int(self.maxSpeedSlider.value), 8, int(self.trimSlider.value), self.lightOn.state]#state gives "down" or "up"

        with open(controlApp.settings_filename, 'w') as fileObject:
            json.dump(self.settings, fileObject)

class controlPage(Widget):
    speedSlider = ObjectProperty(None)
    steeringSlider= ObjectProperty(None)
    connectionMessage = ObjectProperty(None)
    connectButton = ObjectProperty(None)
    speedValue = 0
    steerValue = 0
    device_name = "RoboRoller"
    device_found = False
    socket = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def switchToSettingsPage(self):
        controlApp.screen_manager.transition=SlideTransition(direction = 'left')
        controlApp.screen_manager.current='settingsPage'
    
    def switchToInfoPage(self, *event):
        controlApp.screen_manager.transition = SlideTransition(direction= 'down')
        controlApp.screen_manager.current = 'infoPage'

    def infoButtonPressed(self, *event):
        if self.connectButton.text == "CONNECT":
            self.switchToInfoPage()
        else:
            self.disconnect()
            self.switchToInfoPage()

    def settingsCogPressed(self):
        if self.connectButton.text == "CONNECT":
            self.switchToSettingsPage()
        else:
            self.disconnect()
            self.switchToSettingsPage()

    def speedSliderValueUpdate(self):
        self.speedValue=int(self.speedSlider.value)
    def steerSliderValueUpdate(self):
        self.steerValue=int(self.steeringSlider.value)

    def on_speed_slider_release(self, touch, widget):
        if touch.grab_current == widget:
            #print('my_slider has been released')
            self.speed_back_to_zero=Clock.schedule_once(self.setSpeedSliderZero, 0.7)
    def on_speedSlider_press(self, touch, widget):#works
        if touch.grab_current != widget:
            #print('my slider is pressed')
            try:
                self.speed_back_to_zero.cancel()
            except AttributeError:
                pass
            try:
                self.resetSpeedSliderValue.cancel()
            except AttributeError:
                pass
    def bringSpeedSliderValueOneCloserToZero(self, *clock):
        if self.speedSlider.value > -1 and self.speedSlider.value < 1:
            self.resetSpeedSliderValue.cancel()
            self.speedSlider.value = 0
        elif self.speedSlider.value > 0:
            self.speedSlider.value += -1
        else:
            self.speedSlider.value += 1
    def setSpeedSliderZero(self, *clock):
        self.resetSpeedSliderValue = Clock.schedule_interval(self.bringSpeedSliderValueOneCloserToZero, 0.002)
    
    def on_steer_slider_release(self, touch, widget):
        if touch.grab_current == widget:
            #print('my_slider has been released')
            self.steer_back_to_middle=Clock.schedule_once(self.setSteerSliderZero, 0.7)
    def on_steerSlider_press(self, touch, widget):#works
        if touch.grab_current != widget:
            #print('my slider is pressed')
            try:
                self.steer_back_to_middle.cancel()
            except AttributeError:
                pass
            try:
                self.resetSteerSliderValue.cancel()
            except AttributeError:
                pass
    def bringSteerSliderValueOneCloserToZero(self, *clock):
        if self.steeringSlider.value > -1 and self.steeringSlider.value < 1:
            self.resetSteerSliderValue.cancel()
            self.steeringSlider.value = 0
        elif self.steeringSlider.value > 0:
            self.steeringSlider.value += -1
        else:
            self.steeringSlider.value += 1
    def setSteerSliderZero(self, *clock):
        self.resetSteerSliderValue = Clock.schedule_interval(self.bringSteerSliderValueOneCloserToZero, 0.002)

    #def printValues(self, clock):
        #print('Speed: ' + str(int(self.speedValue)) + ',  Steering: ' + str(int(self.steerValue)))

    def connectButtonPressed(self, *instance):
        if self.connectButton.text == "CONNECT":
            self.connectionMessage.text = "Connecting..."
            Clock.schedule_once(self.connect)
        else:
            self.disconnect()

    def connect(self, *instance):
        try:
            with open(controlApp.settings_filename, 'r') as file_object:
                    self.settings = json.load(file_object)
            self.settingsString = ""
            self.settingsString += str(self.settings[0])
            self.settingsString += "," 
            self.settingsString += str(self.settings[1])
            self.settingsString += ","
            self.settingsString += str(self.settings[2])
            self.settingsString += ","
            if(self.settings[3] == 'down'):
                self.settingsString += "1"
            else:
                self.settingsString += "0"
        except FileNotFoundError:
            self.settings[0] = 50
            self.settings[1] = 100
            self.settings[2] = 0
            self.settings[3] = 'down'
            self.settingsString = ""
            self.settingsString += str(self.settings[0])
            self.settingsString += "," 
            self.settingsString += str(self.settings[1])
            self.settingsString += ","
            self.settingsString += str(self.settings[2])
            self.settingsString += ","
            if(self.settings[3] == 'down'):
                self.settingsString += "1"
            else:
                self.settingsString += "0"
            self.connectionMessage.text = "It is recommended to set settings before proceeding.\nDefault settings are currently being used."
            Clock.schedule_once(self.deleteConnectionMessage, 7)
        
        #Important connection code below
        try:
            nearby_devices = controlApp.bluetooth_adapter.getBondedDevices().toArray()#Get a list of nearby devices (Devices set up once before in settings)
            self.device_found = False
            target_device = None
            
            for device in nearby_devices:
                if device.getName() == self.device_name:#If the name matches the one specified, connect
                    target_device = device
                    self.device_found = True

                    self.socket = target_device.createRfcommSocketToServiceRecord(target_device.getUuids()[0].getUuid())
                    self.socket.connect()
                    #Code above establishes a connection

                    self.outputStream = self.socket.getOutputStream()
                    #Establishes an output stream you can write to
                    #End of important connection code

                    self.setupRoboRoller = Clock.schedule_interval(self.setSettings, 0.075)
                    self.startDataFlow = Clock.schedule_once(self.startSending, 2)

                    self.connectionMessage.text = "Connected Successfully!"
                    self.connectButton.text = "DISCONNECT"
                    Clock.schedule_once(self.deleteConnectionMessage, 15)
                    break

        except:
            self.deleteConnectionMessage()
            controlApp.screen_manager.transition = SwapTransition(duration = 1)
            controlApp.screen_manager.current = 'connectionErrorPage'

        if self.device_found == False:
            self.deleteConnectionMessage()
            controlApp.screen_manager.transition = SwapTransition(duration = 1)
            controlApp.screen_manager.current = 'connectionErrorPage'

    def send_data(self, *clock):
        self.data = str(self.speedValue) + "," + str(self.steerValue)
        print(self.data)
        self.data = "   " + self.data + ";"
        #Important code to send data
        try:
            self.outputStream.write(self.data.encode())#Write to output stream-Sends a string through bluetooth
        except:
            self.disconnect()
            #End of important code in the method
            self.connectionMessage.text = "ERROR:\nRoboRoller Disconnected"
            Clock.schedule_once(self.deleteConnectionMessage, 5)

    def disconnect(self, *instance):
        self.dataFlow.cancel()
        #Important code for disconnect
        if self.socket is not None:#if there is a connection:
            self.socket.close()#Closes the connection
            self.socket = None
        #End of important code

        self.connectButton.text = "CONNECT"

    def setSettings(self, *clock):
        try:
            self.setupData = "     "
            self.setupData += "3625,"
            self.setupData += self.settingsString
            self.setupData += ";"
            self.outputStream.write(self.setupData.encode())
        except:
            controlApp.screen_manager.transition = SwapTransition(duration = 1)
            controlApp.screen_manager.current = 'connectionErrorPage'
            self.socket.close()
    
    def startSending(self, *clock):
        self.setupRoboRoller.cancel()
        self.dataFlow = Clock.schedule_interval(self.send_data, 0.08)

    def deleteConnectionMessage(self, *clock):
        self.connectionMessage.text = ""

    def stop(self, *event):
        self.steeringSlider.value = 0
        self.speedSlider.value = 0
            
class connectionErrorPage(Widget):

    def goBack(self, *event):
        controlApp.screen_manager.transition = SwapTransition(duration = 1)
        controlApp.screen_manager.current = 'controlPage'

class RCcontrollerApp(App):

    settings_filename = 'RCCarControllerSettingsAndroid.json'
    
    def build(self):
        Builder.load_file("RCcontrol.kv")
        self.settingsExist = os.path.exists(self.settings_filename)
        self.screen_manager = ScreenManager()

        self.blankPage = blankPage()
        self.screen = Screen(name = 'blankPage')
        self.screen.add_widget(self.blankPage)
        self.screen_manager.add_widget(self.screen)


        self.welcomePage = welcomePage()
        self.screen = Screen(name = 'welcomePage')
        self.screen.add_widget(self.welcomePage)
        self.screen_manager.add_widget(self.screen)

        self.infoPage = infoPage()
        self.screen = Screen(name = 'infoPage')
        self.screen.add_widget(self.infoPage)
        self.screen_manager.add_widget(self.screen)

        self.settingsPage = settingsPage()
        self.screen = Screen(name = 'settingsPage')
        self.screen.add_widget(self.settingsPage)
        self.screen_manager.add_widget(self.screen)

        self.controlPage = controlPage()
        self.screen = Screen(name = 'controlPage')
        self.screen.add_widget(self.controlPage)
        self.screen_manager.add_widget(self.screen)

        self.connectionErrorPage = connectionErrorPage()
        self.screen = Screen(name = 'connectionErrorPage')
        self.screen.add_widget(self.connectionErrorPage)
        self.screen_manager.add_widget(self.screen)

        self.screen_manager.transition = NoTransition()
        self.screen_manager.current = 'blankPage'

        Clock.schedule_once(self.start, 0.1)

        
        #Clock.schedule_interval(self.controlPage.printValues, 1)

        return self.screen_manager
    
    def start(self, *clock):
        self.screen_manager.transition=FadeTransition(duration = 0.4)

        self.bluetooth_adapter = BluetoothAdapter.getDefaultAdapter()

        if not self.bluetooth_adapter.isEnabled():
            self.bluetooth_adapter.enable()

        if self.settingsExist:
            self.screen_manager.current='controlPage'
        else:
            self.screen_manager.current='welcomePage'

if __name__=="__main__":
    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
    BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
    BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')

    controlApp = RCcontrollerApp()
    controlApp.run()
