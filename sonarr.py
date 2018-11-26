#!/home/jnave/tgbot/bin/python
import requests, json, configparser, logging, sys

class sonarrApi():
    def __init__(self):
        self.log = logging
        self.log.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',filename='sonarr_api.log', filemode='w',
                level=logging.INFO)
        self.config = configparser.ConfigParser()
        self.sonarr_url = ""
        self.sonarr_token = ""

    def load_config(self, configfile):
        """
        the config here should be in 
        windows ini format at min it
        needs common and sonarr sections
        """
        try:
            self.config.read(configfile)
            self.sonarr_url = self.config['SONARR']['url']
            self.sonarr_token = self.config['SONARR']['token']
            try:
                self.sonarr_basic_user = self.config['SONARR']['basic_user']
                self.sonarr_basic_pass = self.config['SONARR']['basic_pass']
            except:
                self.log.warn("no basic user passed")
        except:
            self.log.error("Error reading config file {}".format(configfile))
            sys.exit(1)

    def search_series(self, search):
        """
        this will search for a show 
        it replaces spaces wiht %20
        in order to properly search
        it will return a dict from
        return_titles
        """
        search.replace(' ', '%20')
        """
        if self.sonarr_basic_user:
            self.url = str(self.sonarr_url + "/api/series/lookup?term=" +
                    search + "&apikey=" + self.sonarr_token)
            self.r = requests.get(self.url, auth=(self.sonarr_basic_user, self.sonarr_basic_pass))
        else:
            self.r = requests.get(self.sonarr_url + "/api/" + search +
                    "&apikey=" + self.sonarr_token)
        try:
            self.log.info("titles are: {}".format(self.return_titles(self.r.text)))
            return self.return_titles(self.r.text)
        except:
            self.log.error("failed on return_titles")
        """
        self.url = str(self.sonarr_url + "/api/series/lookup?term=")
        try:
            self.log.info("titles are: {}".format(self.return_titles(self.do_tv_search(self.url, search))))
            return self.return_titles(self.do_tv_search(self.url, search))
        except:
            self.log.error("failed on do_tv_search or return_titles")

    def return_titles(self, rawjson):
        """
        this just populates the fields we want into a dict
        """
        self.titles = {}
        try:
            self.showlist = rawjson
        except:
            self.log.error("failed to load json in return_titles")
            pass
        for show in self.showlist:
            self.titles[show['title']] = show['tvdbId']
        return self.titles
    
    def in_library(self, tvdbId):
        """
        returns true if the tbdbId
        is found in the library
        """
        self.url = str(self.sonarr_url + "/api/series")
        jdata = self.do_tv_search(self.url)
        self.log.info("passed arg is: ".format(tvdbId))
        for show in jdata:
            if show['tvdbId'] == int(tvdbId):
                return True
                break
        return False

    def do_tv_search(self, url, search_term = False):
        """
        returns a json object of the results
        or returns false if nothing is found
        """
        if search_term:
            url += search_term
            url += "&apikey=" + self.sonarr_token
        else:
            url += "?apikey=" + self.sonarr_token
        if self.sonarr_basic_user:
            self.r = requests.get(url, auth=(self.sonarr_basic_user, self.sonarr_basic_pass))
        else:
            self.r = requests.get(url)
        if self.r.status_code == 200:
            return json.loads(self.r.text)
        else:
            return False

    def add_series(self, tvdbId):
        """
        this will create the post URL
        to download a series it will
        return true if the post worked
        false otherwise
        """
        try:
            self.gurl = str(self.sonarr_url + "/api/series/lookup" + "?term=tvdbId:")
        except:
            self.log.error("problem with gurl")
        self.log.info("Got request for tbdbId: {}".format(tvdbId))
        raw_data = self.do_tv_search(self.gurl, str(tvdbId))
        self.used_fields = ['tvdbId', 'tvTageId', 'title', 'titleSlug', 'images', 'seasons']
        self.used_fields_optional = [{'addOptions': {'ignoreEpisodesWithFiles':
                                                     'true',
                                                     'ignoreEpisodesWithoutFiles':
                                                     'false',
                                                     'searchForMissingEpisodes':
                                                     'true'}},
                                     {'rootFolderPath': '/media/TV/'}]
        self.purl = str(self.sonarr_url + "/api/series/" + "?apikey=" + self.sonarr_token)
        self.pdata = {}
        for show in raw_data:
            for key, value in show.items():
                if key in self.used_fields:
                    self.pdata[key] = value
        self.pdata['qualityProfileId'] = 1
        for x in self.used_fields_optional:
            for k, v in x.items():
                self.pdata[k] = v
        try:
            self.jpdata = json.dumps(self.pdata)
        except:
            self.log.error("Couldn't load {} as json object".format(self.pdata))
        self.log.info("JSON DATA IS: \n {}".format(self.jpdata))
        self.pr = requests.post(self.purl, data=self.jpdata, auth=(self.sonarr_basic_user, self.sonarr_basic_pass))
        self.log.warn("For post request i got back: {}".format(self.pr.status_code, self.pr.text))
        if self.pr.status_code == 201:
            return True
        else:
            return False

if __name__ == "__main__":
    api = sonarrApi()
    api.load_config('dlconfig.cfg')
    api.search_series("Rick and")
