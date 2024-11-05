from datetime import datetime
import requests
import time

# Define the headers for authentication
headers = {
    'api-key': '1fbec931-828d-4ad7-86b6-a86a23528d8b',
    'Content-Type': 'application/json',
    'account-id': '2c2feb70b918/484484fa-6523-4472-8b47-9ee034569fa'
}

def authenticate_license(dob, license_id):
    """
    Calls an API to initiate the authentication process, generating a request ID.
    """
    # Set up the API endpoint and payload for the initial license authentication request
    url = 'https://eve.idfy.com/v3/tasks/async/verify_with_source/ind_driving_license'
    payload = {
        "task_id": "74f4c926-250c-43ca-9c53-453e87ceacd1",
        "group_id": "8e16424a-58fc-4ba4-ab20-5bc8e7c3c41e",
        "data": {
            "id_number": license_id,
            "date_of_birth": dob,
            "advanced_details": {
                "state_info": True,
                "age_info": True,
                "profile_image_info": True  # Request profile image
            }
        }
    }
    
    # Perform the POST request to generate a new request_id
    response = requests.post(url, json=payload, headers=headers)
    response=response.json()
    time.sleep(3)
    if response['request_id'] :
      print(response['request_id'])
      return  get_license_task(response['request_id'],license_id)
    else:
        print(f"Error: {response.status_code}")
        return None


# def get_license_task(request_id):
#     """
#     Fetches license information from the API using the generated request ID.
#     """
#     url = f'https://eve.idfy.com/v3/tasks?request_id={request_id}'
    
#     # Perform the GET request
#     response = requests.get(url, headers=headers)
    
#     if response:
#         data = response.json()
      
#         data=data[0]['result']['source_output']
      
#         result = data
#         print(result, 'ressssssssssssssssssssss')
#         # Extract specific fields from the response
#         license_info = {
       
#             'name': result['name'],
#             'date_of_last_transaction': result.get('date_of_last_transaction'),
#             'dl_status': result.get('dl_status'),
#             'nt_validity_from': result.get('nt_validity_from'),
#             'nt_validity_to': result.get('nt_validity_to'),
          
        
#         }
        
#         return license_info
    
#     else:
#         return {'error': 'Failed to retrieve data', 'status_code': response.status_code}

def get_license_task(request_id ,license_id):
    """
    Fetches license information from the API using the generated request ID.
    """
    url = f'https://eve.idfy.com/v3/tasks?request_id={request_id}'
    
    # Perform the GET request
    response = requests.get(url, headers=headers)
    
    if response:
        data = response.json()
        result = data[0]['result']['source_output']
        
        # Extract specific fields from the response
        license_info = {
            'name': result.get('name'),
            'license_id':license_id,
            'nt_validity_from': result.get('nt_validity_from'),
            'nt_validity_to': result.get('nt_validity_to'),
        }
        
        # Check if the current date is within the validity period
        try:
            nt_validity_from = datetime.strptime(license_info['nt_validity_from'], "%Y-%m-%d")
            nt_validity_to = datetime.strptime(license_info['nt_validity_to'], "%Y-%m-%d")
            current_date = datetime.now()
            
            # Determine the status based on the current date
            license_info['status'] = 'Active' if nt_validity_from <= current_date <= nt_validity_to else 'Expired'
        
        except (TypeError, ValueError):
            license_info['status'] = 'Invalid dates'  # Handle missing or improperly formatted dates

        print(license_info, 'ressssssssssssssssssssss')
        return license_info
    
    else:
        return {'error': 'Failed to retrieve data', 'status_code': response.status_code}
# # Usage example
# dob = "2002-07-29"  # Replace with the actual date of birth
# license_id = "TS10820210003526"  # Replace with the actual license ID

