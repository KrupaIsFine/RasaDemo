# # This files contains your custom actions which can be used to run
# # custom Python code.
# #
# # See this guide on how to implement these action:
# # https://rasa.com/docs/rasa/custom-actions


# # This is a simple example for a custom action which utters "Hello World!"
from rasa_sdk import Action, Tracker, FormValidationAction
from typing import Text, List, Dict, Any
import os
from datetime import datetime
from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import AllSlotsReset
import requests
from rasa_sdk.events import SlotSet, EventType
import json

order_details = [
    {"order_id": "TV00000001", "cust_ref": "DCLOG23-AB-00015", "weight": "10kg", "completed": False},
    {"order_id": "TV00000002", "cust_ref": "DCLOG23-AT-00215", "weight": "100kg", "completed": False},
    {"order_id": "TV00000003", "cust_ref": "DCLOG23-AC-00015", "weight": "40kg", "completed": False},
    {"order_id": "TV00000004", "cust_ref": "DCLOG23-AC-00035", "weight": "55kg", "completed": False},
    {"order_id": "TV00000005", "cust_ref": "DCLOG23-AC-00045", "weight": "70kg", "completed": False},
    {"order_id": "TV00000006", "cust_ref": "DCLOG23-AC-00055", "weight": "20kg", "completed": False},
    # ... more orders ...
]

class ActionDisplayDetails(Action):

    def name(self) -> Text:
        return "action_display_details"

    def run(self, dispatcher, tracker, domain):

        available_orders = [order for order in order_details if not order["completed"]]
        print("available orders:", available_orders)
        payloads = []  # Initialize an empty list to store payloads

        buttons = []

        for order in available_orders:
            payload = f'/select_order{{"option": "{order["order_id"]}"}}'
            payloads.append(payload)  # Store the payload in the list
            buttons.append({
                "title": f"{order['order_id']}",
                "payload": payload
            })
            
        dispatcher.utter_message(text="Heres your order details", buttons=buttons, button_type="vertical")

        return []  # Reset the slot value


class ActionGetLocation(Action):

    def name(self) -> Text:
        return "action_get_location"

    def run(self, dispatcher, tracker, domain):
        
        latlong = tracker.get_slot("latlong")
        print("latlong", latlong) 
        return [SlotSet("latlong", latlong)]

class ActionCompleteOrder(Action):

    def name(self) -> Text:
        return "action_complete_order"

    def run(self, dispatcher, tracker, domain):
        
        selected_order_id = tracker.get_slot("selected_order_id")
        print("order id", selected_order_id) 
        # Validate order
        if not selected_order_id:
            dispatcher.utter_message(text="No order ID provided.") 
            return []
        for order in order_details:
            if order["order_id"] == selected_order_id:
                order["completed"] = True
        print("after order details", order_details)
        return [SlotSet("order_id", None)]



class ActionHandleButtonClick(Action):
    def name(self) -> Text:
        return "action_handle_button_click"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Extract relevant information from the payload
        selected_order_id = tracker.latest_message.get("text")
        print("order id", selected_order_id) 
        start_quote = selected_order_id.rfind('"')  # Find the index of the last double quote
        end_quote = selected_order_id.rfind('"', 0, start_quote)  # Find the index of the second last double quote
        selected_order_id = selected_order_id[end_quote + 1 : start_quote]
        print("order id", selected_order_id)  # Extract the value between the quotes
        # Set the dynamic slot with the selected order ID
        return [SlotSet("selected_order_id", selected_order_id)]


class ActionDisplayOrderDetails(Action):
    def name(self) -> Text:
        return "action_display_order_details"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Retrieve order details from tracker or any external source
        selected_order_id = tracker.get_slot("selected_order_id")
        print("selected is", selected_order_id)
        customer_reference = "DCLOG23-AB-00015" #tracker.get_slot("customer_reference")
        weight = "10kg" #tracker.get_slot("weight")
        latlong = tracker.get_slot("latlong")  
        # Prepare the response message
        response = f"Here are the order details: ID: {selected_order_id}, Customer Reference: {customer_reference}, Weight: {weight}, Latlong: {latlong}"

        dispatcher.utter_message(text=response)

        return []

def save_image_locally(image_url, save_path):
    response = requests.get(image_url)
    if response.status_code == 200:
        print("inside loop")
        with open(save_path, 'wb') as file:
            file.write(response.content)
        return True
    else:
        return False

class ActionSayData(Action):
    def name(self) -> Text:
        return "action_say_data"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Retrieve order details from tracker or any external source
        selected_order_id = tracker.get_slot("selected_order_id")
        username = tracker.get_slot("username")        
        lpn_count = tracker.get_slot("lpn_count")  
        file_id = None

        for event in tracker.events:
            if 'metadata' in event and 'message' in event['metadata']:
                message = event['metadata']['message']
                if 'photo' in message and len(message['photo']) > 0:
                    file_id1 = message['photo'][0]['file_id']
                    if file_id != file_id1:
                        print("file id", file_id1)
                        file_id = file_id1
                        image_url = "https://api.telegram.org/bot6094629106:AAH5dKGlZuHQ6yvF4wOY9JPFGcVQGE8YRuc/getFile?file_id=" + file_id
                        response = requests.get(image_url)
                        # Parse the API response as JSON data
                        json_data = response.json()

                        # Access the file ID and file path
                        file_id = json_data["result"]["file_id"]
                        file_path = json_data["result"]["file_path"]

                        # Print the extracted file ID and file path
                        print("File ID:", file_id)
                        print("File Path:", file_path)
                        if response.status_code == 200:        
                                image_url = "https://api.telegram.org/file/bot6094629106:AAH5dKGlZuHQ6yvF4wOY9JPFGcVQGE8YRuc/" + file_path
                        else:
                            # Handle the case when the API request is not successful
                            failure_message = "API request failed. Please try again later."
                            dispatcher.utter_message(text=failure_message)
                    else:
                        continue
                    break  # Stop iterating once the file_id is found
        # Download the image using Telegram Bot API
        picture = "Picture Uploaded"  
        
        # Save the image locally
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        image_filename = f"image_{timestamp}.jpg"

        # Specify the directory path where the image file will be saved
        image_directory = r"C:\\Users\\Krupavathi\\Desktop\\SMC-PG\\Internship"

        # Construct the full file path by joining the directory path and filename
        save_path = os.path.join(image_directory, image_filename)
        
        if save_image_locally(image_url, save_path):
            print("Image saved successfully.")
        else:
            print("Failed to save image.")
            
        # Prepare the response message
        response = f"Here are the details: OrderId: {selected_order_id} Name: {username}, Lpn no: {lpn_count}, Pob Image: {picture}"
        dispatcher.utter_message(text=response)

        return []


class ActionExtractLocation(Action):
    def name(self) -> Text:
        return "action_extract_location"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_location = tracker.get_slot("location")
        if user_location:
            latitude = user_location["latitude"]
            longitude = user_location["longitude"]
            # You can now use the latitude and longitude for further processing
            # For example, you can store it in a slot or use it to fetch location-specific data
            dispatcher.utter_message(f"Received location: Latitude - {latitude}, Longitude - {longitude}")
        else:
            dispatcher.utter_message("No location received.")
        return []

class ActionResetFormSlotsPob(Action):
    def name(self) -> Text:
        return "action_reset_form_slots_pob"

    def run(self, dispatcher, tracker, domain):
        # Get POD form action class
        pob_form = pob_form()

        # Reset POD form slots
        pob_form.reset()

        return []

class ActionResetFormSlotsPod(Action):
    def name(self) -> Text:
        return "action_reset_form_slots_pod"

    def run(self, dispatcher, tracker, domain):
        # Get POD form action class
        pod_form = pod_form()

        # Reset POD form slots
        pod_form.reset()

        return []


class ActionResetSlots(Action):

     def name(self) -> Text:
            return "action_reset_slots"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # List of slot names to reset
        slots_to_reset = ["username", "lpn_count", "picture"]

        return [SlotSet(slot_name, None) for slot_name in slots_to_reset]
