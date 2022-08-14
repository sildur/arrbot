import configparser
import json
import logging
import requests
import sys


def return_titles(raw_json):
    """
    this just populates the fields we want into a dict
    """
    titles = {}
    for movie in raw_json:
        for k, v in movie.items():
            if k == "tmdbId":
                title_key = movie["title"] + "(" + str(movie["year"]) + ")"
                titles[title_key] = v
    return titles


class RadarrApi:
    """
    module to interact with a radarr
    instance. It has a few methods exposed
    some are internal only, so keep that in mind
    when in doubt, read the code
    """
    gurl: str

    def __init__(self):
        self.log = logging
        self.log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='radarr_api.log',
                             filemode='w',
                             level=logging.INFO)
        self.config = configparser.ConfigParser()
        self.radarr_url = ""
        self.radarr_token = ""
        self.root_folder_path = ""
        self.used_fields_optional = []
        self.used_fields = ['tmdbId', 'title', 'titleSlug',
                            'images', 'year']
        self.radarr_basic_user = False
        self.radarr_basic_pass = False

    def load_config(self, configfile):
        """
        the config here should be in 
        windows ini format at min it
        needs common and radarr sections
        """
        try:
            self.config.read(configfile)
            self.radarr_url = self.config['radarr']['url']
            self.radarr_token = self.config['radarr']['token']
            self.root_folder_path = self.config['radarr']['root_folder_path']
            self.used_fields_optional = [{'monitored': True},
                                         {'rootFolderPath': self.root_folder_path},
                                         {'addOptions': {'searchForMovie': True}}]
            try:
                self.radarr_basic_user = self.config['common']['basic_user']
                self.radarr_basic_pass = self.config['common']['basic_pass']
            except:
                self.radarr_basic_user = False
                self.radarr_basic_pass = False
                self.log.warning("no basic user passed")
        except KeyError:
            self.log.error("Error reading config file {}".format(configfile))
            sys.exit(1)

    def search_movie(self, search):
        """
        this will search for a show 
        it replaces spaces with %20
        in order to properly search
        it will return a dict from
        return_titles
        """
        search.replace(' ', '%20')
        url = str(self.radarr_url + "/api/v3/movie/lookup?term=")
        self.log.info("Searching for: {}".format(search))
        try:
            returned_value = return_titles(self.do_movie_search(url, search))
            return returned_value
        except:
            self.log.error("failed on do_movie_search or return_titles for {}".format(search))

    def in_library(self, tmdb_id):
        """
        returns true if the tbdbId
        is found in the library
        """
        url = str(self.radarr_url + "/api/v3/movie")
        jdata = self.do_movie_search(url)
        for show in jdata:
            if show['tmdbId'] == int(tmdb_id):
                return True
        return False

    def do_movie_search(self, url, search_term=None):
        """
        returns a json object of the results
        or returns false if nothing is found
        """
        if search_term:
            url += search_term
            url += "&apikey=" + self.radarr_token
        else:
            url += "?apikey=" + self.radarr_token
        if self.radarr_basic_user:
            request = requests.get(url, auth=(self.radarr_basic_user, self.radarr_basic_pass))
        else:
            request = requests.get(url)
        if request.status_code == 200:
            return json.loads(request.text)
        else:
            self.log.error("Status Code: {}".format(request.status_code))
            self.log.error("Text returned: {}".format(request.text))
            return False

    def add_movie(self, tmdb_id):
        """
        this will create the post URL
        to download a movie it will
        return true if the post worked
        false otherwise
        """
        jpdata = {}
        try:
            self.gurl = str(self.radarr_url + "/api/v3/movie/lookup/tmdb" + "?tmdbId=")
        except:
            self.log.error("problem with {}".format(self.gurl))
        self.log.info("Got request for tbdbId: {}".format(tmdb_id))
        raw_data = self.do_movie_search(self.gurl, str(tmdb_id))
        post_url = str(self.radarr_url + "/api/v3/movie/" + "?apikey=" + self.radarr_token)
        try:
            jpdata = json.dumps(self.build_data(raw_data))
        except:
            self.log.error("Couldn't load {} as json object".format(jpdata))
        headers = {'Content-type': 'application/json'}
        try:
            post_request = requests.post(
                post_url, data=jpdata, headers=headers,
                auth=(self.radarr_basic_user, self.radarr_basic_pass)
            )
        except:
            self.log.error("Got {} from api".format(post_request.status_code))
        if post_request.status_code == 201:
            return True
        else:
            return False

    def build_data(self, data):
        """
        builds json data from raw response
        asdf
        """
        built_data = {'qualityProfileId': 1}
        for key, value in data.items():
            if key in self.used_fields:
                built_data[key] = value
        for x in self.used_fields_optional:
            for k, v in x.items():
                built_data[k] = v
        return built_data

