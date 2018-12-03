#!/home/jnave/tgbot/bin/python
import requests, json, configparser, logging, sys


class radarrApi():
    gurl: str

    def __init__(self):
        self.log = logging
        self.log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='radarr_api.log',
                             filemode='w',
                             level=logging.INFO)
        self.config = configparser.ConfigParser()
        self.radarr_url = ""
        self.radarr_token = ""
        self.used_fields = ['tmdbId', 'title', 'titleSlug',
                            'images', 'year']
        self.used_fields_optional = [{'monitored': 'True'},
                                     {'rootFolderPath': '/media/movies/'}]

    def load_config(self, configfile):
        """
        the config here should be in 
        windows ini format at min it
        needs common and radarr sections
        """
        try:
            self.config.read(configfile)
            self.radarr_url = self.config['RADARR']['url']
            self.radarr_token = self.config['RADARR']['token']
            try:
                self.radarr_basic_user = self.config['COMMON']['basic_user']
                self.radarr_basic_pass = self.config['COMMON']['basic_pass']
            except:
                self.log.warn("no basic user passed")
        except:
            self.log.error("Error reading config file {}".format(configfile))
            sys.exit(1)

    def search_movie(self, search):
        """
        this will search for a show 
        it replaces spaces wiht %20
        in order to properly search
        it will return a dict from
        return_titles
        """
        search.replace(' ', '%20')
        self.url = str(self.radarr_url + "/api/movie/lookup?term=")
        try:
            self.log.info("titles are: {}".format(self.return_titles(self.do_movie_search(self.url, search))))
            return self.return_titles(self.do_movie_search(self.url, search))
        except:
            self.log.error("failed on do_movie_search or return_titles")

    def return_titles(self, rawjson):
        """
        this just populates the fields we want into a dict
        """
        self.titles = {}
        for movie in rawjson:
            for k, v in movie.items():
                if k == "tmdbId":
                    tkey = movie["title"] + "(" + str(movie["year"]) + ")"
                    self.titles[tkey] = v
        return self.titles

    def in_library(self, tmdbId):
        """
        returns true if the tbdbId
        is found in the library
        """
        self.url = str(self.radarr_url + "/api/movie")
        jdata = self.do_movie_search(self.url)
        for show in jdata:
            if show['tmdbId'] == int(tmdbId):
                return True
                break
        return False

    def do_movie_search(self, url, search_term=False):
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
            self.r = requests.get(url, auth=(self.radarr_basic_user, self.radarr_basic_pass))
        else:
            self.r = requests.get(url)
        if self.r.status_code == 200:
            return json.loads(self.r.text)
        else:
            self.log.error("Status Code: {}".format(self.r.status_code))
            self.log.error("Text returned: {}".format(self.r.text))
            return False

    def add_movie(self, tmdbId):
        """
        this will create the post URL
        to download a movie it will
        return true if the post worked
        false otherwise
        """
        jpdata = {}
        try:
            self.gurl = str(self.radarr_url + "/api/movie/lookup/tmdb" + "?tmdbId=")
        except:
            self.log.error("problem with {}".format(self.gurl))
        self.log.info("Got request for tbdbId: {}".format(tmdbId))
        raw_data = self.do_movie_search(self.gurl, str(tmdbId))
        self.purl = str(self.radarr_url + "/api/movie/" + "?apikey=" + self.radarr_token)
        try:
            jpdata = json.dumps(self.build_data(raw_data))
        except:
            self.log.error("Couldn't load {} as json object".format(jpdata))
        try:
            self.pr = requests.post(self.purl, data=jpdata, auth=(self.radarr_basic_user, self.radarr_basic_pass))
        except:
            self.log.error("Got {} from api".format(self.pr.status_code))
        if self.pr.status_code == 201:
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

if __name__ == "__main__":
    api = radarrApi()
    api.load_config('dlconfig.cfg')
    api.search_movie("Rick and")
