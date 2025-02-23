from openai import OpenAI
import json
import pydantic
import requests
import time
import os


class Location(pydantic.BaseModel):
    latitude: float
    longitude: float
    displayName: str
    rating: float


class DisplayNames(pydantic.BaseModel):
    text: str
    languageCode: str


class CityWalkResponse(pydantic.BaseModel):
    locations: list[Location]
    speech: str



poi = [
# 'cultural_landmark *',
# 'historical_place *',
# 'monument *',
# 'museum',
# 'performing_arts_theater',
# 'sculpture *',
# 'library',
# 'university',
# 'adventure_sports_center *',
# 'amphitheatre',
# 'amusement_center',
# 'amusement_park',
# 'aquarium',
# 'banquet_hall',
# 'barbecue_area *',
# 'botanical_garden *',
# 'bowling_alley',
# 'comedy_club *',
# 'community_center',
# 'concert_hall *',
# 'convention_center',
# 'cultural_center',
# 'cycling_park *',
# 'dance_hall *',
# 'dog_park',
# 'event_venue',
# 'garden *',
# 'hiking_area *',
# 'historical_landmark',
# 'karaoke',
# 'marina',
# 'movie_rental',
# 'movie_theater',
# 'national_park',
# 'observation_deck *',
# 'off_roading_area *',
# 'opera_house*',
# 'philharmonic_hall',
# 'picnic_ground',
# 'planetarium *',
# 'skateboard_park',
# 'state_park *',
'tourist_attraction',
# 'video_arcade *',
# 'visitor_center',
# 'water_park',
# 'wedding_venue',
# 'wildlife_park *',
# 'zoo'
]




class CityWalkAgent:
    def __init__(self):
        self.memory = {}
        self.conversation = {}
        self.client = OpenAI()
        self.system_prompt = """
            You are a professional Personal Tour Guide. You are taking a visitor on a city walk. 
            You will be provided with a list of information about the city and the visitor's interests.
            You will need to use this information to answer the visitor's questions and provide them with a memorable experience.
            You should always ask some clarifying questions to understand the visitor's interests and preferences.
            Whenever you provide a recommendation, you must provide a list of locations and a speech response.
            Try your best to provide the list of locations that provide the best route for the visitor to take, so they don't have to backtrack.
            
            Here are some examples of the types of responses you might provide:
            Make sure the tone is relaxed and friendly, some jokes or light-hearted comments are always welcome.
            
            JSON example 1: location recommnedations:
            {
                "locations": ['location 1', 'location 2', 'location 3', ..., 'location N'],
                "speech": "Hi, what about try talking a walk from location 1 to location N? it should take you about 2 hours and you will see some interesting places on the way."
            }

            JSON example 2: clarifying questions: the goal is to get more information from the visitor to refine the recommendations
            {
                "locations": [],
                "speech": "to get started, could you tell me a bit more about what you are interested in seeing? or how much time you would like to spent?"
            }
            
            JSON examples 3: general information: providing information about the point of interest
            {
                "locations": [],
                "speech": "Great Mall is built in 1992 and is the largest shopping mall in the city. It has over 200 stores and a food court with a variety of options."
            }

            JSON examples 4: greeting: greeting the visitor
            {
                "locations": [],
                "speech": "Hello! I am your personal tour guide. I will help you explore the city and find the best places to visit. What would you like to see today?"
            }

            JSON examples 5: revised recommendations: providing revised recommendations based on the visitor's feedback
            {
                "locations": ['location 1', 'location 2', 'location 3', ..., 'location N'],
                "speech": "Based on what you told me, I think you would enjoy visiting location 1, location 2, and location N. Would you like to know more about these places?"
            }

            JSON examples 6: reset conversation: reset the conversation to the beginning, for example, if the visitor's says something like let's restart, start over, etc.
            {
                "locations": [],
                "speech": "Sure! Let's start over. What would you like to see today?"
            }

        """
        self.conversation = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

    def conversation_reset(self):
        self.conversation = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

    def get_nearby_landmarks(self, city):

        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': os.getenv('GOOGLE_API_KEY'),
            'X-Goog-FieldMask': 'places.displayName,places.location,places.rating',
        }

        json_data = {
            'includedTypes': [
                poi
            ],
            'maxResultCount': 20,
            'locationRestriction': {
                'circle': {
                    'center': {
                        'latitude': city['latitude'],
                        'longitude': city['longitude'],
                    },
                    'radius': 5000.0,
                },
            },
        }

        response = requests.post('https://places.googleapis.com/v1/places:searchNearby', headers=headers, json=json_data)
        places = response.json()['places']
        # pop location and repopulate with values
        for place in places:
            location = place.pop('location')
            rating = place.pop('rating', 0)
            displayName = place.pop('displayName')
            place['location'] = location
            place['location']['displayName'] = displayName
            place['location']['rating'] = rating
        return places


    def answer(self, query, metadata):
        city = metadata.city.dict()
        print(f"Query: {query}")
        print(f"City: {city}")
        # time to get the landmarks
        start = time.time()
        landmarks = self.get_nearby_landmarks(city)
        end = time.time()
        print(f"Time to get landmarks: {end - start}")
        # time to get the response
        start = time.time()
        new_message = {
                "role": "user",
                "content": json.dumps({
                    "current_city": city,
                    "near_by_landmarks": landmarks,
                    "new_query": query
                })
            }
        print(f"New Conversation: {self.conversation + [new_message]}")
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o",
            temperature=1,
            max_tokens=4000,
            top_p=1,
            messages=self.conversation + [new_message],
            response_format=CityWalkResponse
        )
        end = time.time()
        print(f"Time to get openai response: {end - start}")
        

        response = completion.choices[0].message.dict()['parsed']
        new_response = {
            "role": "assistant",
            "content": response['speech']
        }
        self.conversation.append(new_message)
        self.conversation.append(new_response)
        return response
    


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    agent = CityWalkAgent()
    # response = agent.answer("What are some interesting places to visit in New York?", "New York", ["Statue of Liberty", "Times Square", "Central Park"])
    # print(response.dict()['parsed'])
    landmarks = agent.get_nearby_landmarks()
    print(landmarks)