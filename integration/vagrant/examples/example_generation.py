import httplib2
import json
import xml.dom.minidom
import sys
import os
from urlparse import urlparse
import time


class ExampleGenerator(object):
    directory = None
    api_url = None
    headers = {}
    tenant = None
    base_url = None
    dbaas_url = None
    replace_host = None

    def __init__(self, config_file):
        if not os.path.exists(config_file):
            raise RuntimeError("Could not find Example CONF at " + config_file + ".")
        file_contents = open(config_file, "r").read()
        try:
            config = json.loads(file_contents)
        except Exception as exception:
            raise RuntimeError("Error loading config file \"" + config_file + "\".",
                exception)

        self.directory = config.get("directory", None)
        if self.directory[-1] != '/':
            self.directory += '/'
        print "directory = %s" % self.directory
        self.api_url = config.get("api_url", None)
        print "api_url = %s" % self.api_url
        #auth
        auth_url = config.get("auth_url", None)
        print "auth_url = %s" % auth_url
        username = config.get("username", None)
        print "username = %s" % username
        password = config.get("password", None)
        print "password = %s" % password
        self.tenant = config.get("tenant", None)
        self.replace_host = config.get("replace_host", None)
        print "tenant = %s" % self.tenant
        auth_id = self.get_auth_token_id(auth_url, username, password)
        print "id = %s" % auth_id
        self.headers['X-Auth-Token'] = auth_id
        self.headers['X-Auth-Project-ID'] = self.tenant
        self.dbaas_url = "%s/v1.0/%s" % (self.api_url, self.tenant)

    def http_call(self, name, url, method, body=None, output=True):
        body = {} if not body else body
        print "http call for %s" % name
        http = httplib2.Http()
        req_headers = {'User-Agent': "python-example-client",
                       'Content-Type': "application/json",
                       'Accept': "application/json"
                      }
        req_headers.update(self.headers)

        content_type = 'json'
        request_body = body.get(content_type, None)
        if output:
            with open("%srequest_%s.%s" % (self.directory, name, content_type), "w") as file:
                output = self.output_request(url, req_headers, request_body, content_type, method)
                if self.replace_host:
                    output = output.replace(self.api_url, self.replace_host)
                    pre_host_port = urlparse(self.api_url).netloc
                    post_host = urlparse(self.replace_host).netloc
                    output = output.replace(pre_host_port, post_host)
                file.write(output)
        json_resp = resp, resp_content = http.request(url, method, body=request_body, headers=req_headers)
        if output:
            with open("%sresponse_%s.%s" % (self.directory, name, content_type), "w") as file:
                output = self.output_response(resp, resp_content, content_type)
                if self.replace_host:
                    output = output.replace(self.api_url, self.replace_host)
                    pre_host_port = urlparse(self.api_url).netloc
                    post_host = urlparse(self.replace_host).netloc
                    output = output.replace(pre_host_port, post_host)
                file.write(output)

        content_type = 'xml'
        req_headers['Accept'] = 'application/xml'
        req_headers['Content-Type'] = 'application/xml'
        request_body = body.get(content_type, None)
        if output:
            with open("%srequest_%s.%s" % (self.directory, name, content_type), "w") as file:
                output = self.output_request(url, req_headers, request_body, content_type, method)
                if self.replace_host:
                    output = output.replace(self.api_url, self.replace_host)
                    pre_host_port = urlparse(self.api_url).netloc
                    post_host = urlparse(self.replace_host).netloc
                    output = output.replace(pre_host_port, post_host)
                file.write(output)
        xml_resp = resp, resp_content = http.request(url, method, body=request_body, headers=req_headers)
        if output:
            with open("%sresponse_%s.%s" % (self.directory, name, content_type), "w") as file:
                output = self.output_response(resp, resp_content, content_type)
                if self.replace_host:
                    output = output.replace(self.api_url, self.replace_host)
                    pre_host_port = urlparse(self.api_url).netloc
                    post_host = urlparse(self.replace_host).netloc
                    output = output.replace(pre_host_port, post_host)
                file.write(output)

        return json_resp, xml_resp

    def output_request(self, url, output_headers, body, content_type, method):
        output_list = []
        parsed = urlparse(url)
        output_list.append("%s %s HTTP/1.1" % (method, parsed.path))
        output_list.append("User-Agent: %s" % output_headers['User-Agent'])
        output_list.append("Host: %s" % parsed.netloc)
        output_list.append("X-Auth-Token: %s" % output_headers['X-Auth-Token'])
        output_list.append("X-Auth-Project-ID: %s" % output_headers['X-Auth-Project-ID'])
        output_list.append("Accept: %s" % output_headers['Accept'])
        output_list.append("Content-Type: %s" % output_headers['Content-Type'])
        output_list.append("")
        pretty_body = self.format_body(body, content_type)
        output_list.append("%s" % pretty_body)
        output_list.append("")
        return '\n'.join(output_list)

    def output_response(self, resp, body, content_type):
        output_list = []
        version = "1.1" if resp.version == 11 else "1.0"
        output_list.append("HTTP/%s %s %s" % (version, resp.status, resp.reason))
        output_list.append("Content-Type: %s" % resp['content-type'])
        output_list.append("Content-Length: %s" % resp['content-length'])
        output_list.append("Date: %s" % resp['date'])
        if body:
            output_list.append("")
            pretty_body = self.format_body(body, content_type)
            output_list.append("%s" % pretty_body)
        output_list.append("")
        return '\n'.join(output_list)

    def format_body(self, body, content_type):
        if content_type == 'json':
            try:
                return json.dumps(json.loads(body), sort_keys=True, indent=4)
            except Exception:
                return body if body else ''
        else:
            # expected type of body is xml
            try:
                return xml.dom.minidom.parseString(body).toprettyxml()
            except Exception:
                return body if body else ''

    def get_auth_token_id(self, url, username, password):
        body = '{"passwordCredentials": {"username": "%s", "password": "%s", "tenantId": "%s"}}' % (username, password, self.tenant)
        http = httplib2.Http()
        req_headers = {'User-Agent': "python-example-client",
                       'Content-Type': "application/json",
                       'Accept': "application/json",
                      }
        resp, body = http.request(url, 'POST', body=body, headers=req_headers)
        auth = json.loads(body)
        auth_id = auth['auth']['token']['id']
        return auth_id

    def wait_for_instances(self):
        example_instances = []
        # wait for instances
        while True:
            url = "%s/instances" % self.dbaas_url
            resp_json, resp_xml = self.http_call("get_instances", url, 'GET', output=False)
            resp_content = json.loads(resp_json[1])
            instances = resp_content['instances']
            print_list = [(instance['id'], instance['status']) for instance in instances]
            print "checking  for : %s\n" % print_list
            list_id_status = [(instance['id'], instance['status']) for instance in instances if
                                                                   instance['status'] in ['ACTIVE', 'ERROR', 'FAILED']]
            if len(list_id_status) == 2:
                statuses = [item[1] for item in list_id_status]
                if statuses.count('ACTIVE') != 2:
                    break
                example_instances = [inst[0] for inst in list_id_status]
                print "\nusing instance ids ---\n%s\n" % example_instances
                # instances should be ready now.
                break
            else:
                time.sleep(15)
        return example_instances

    def check_clean(self):
        url = "%s/instances" % self.dbaas_url
        resp_json, resp_xml = self.http_call("get_instances", url, 'GET', output=False)
        resp_content = json.loads(resp_json[1])
        instances = resp_content['instances']
        if len(instances) > 0:
            raise Exception("Environment must be clean to run the example generator.")
        print "\n\nClean environment building examples...\n\n"

    def get_versions(self):
        #no auth required
        #list versions
        url = "%s/" % self.api_url
        self.http_call("versions", url, 'GET')

    def get_version(self):
        #list version
        url = "%s/v1.0/" % self.api_url
        self.http_call("version", url, 'GET')

    def get_flavors(self):
        # flavors
        url = "%s/flavors" % self.dbaas_url
        self.http_call("flavors", url, 'GET')

    def get_flavor_details(self):
        #flavors details
        url = "%s/flavors/detail" % self.dbaas_url
        self.http_call("flavors_detail", url, 'GET')

    def get_flavor_by_id(self):
        #flavors by id
        url = "%s/flavors/1" % self.dbaas_url
        self.http_call("flavors_by_id", url, 'GET')

    def post_create_instance(self):
        #create instance json
        url = "%s/instances" % self.dbaas_url
        JSON_DATA = {
            "instance": {
                "name": "json_rack_instance",
                "flavorRef": "%s/flavors/1" % self.dbaas_url,
                "databases": [
                        {
                        "name": "sampledb",
                        "character_set": "utf8",
                        "collate": "utf8_general_ci"
                    },
                        {
                        "name": "nextround"
                    }
                ],
                "volume":
                        {
                        "size": "2"
                    }
            }
        }
        XML_DATA = ('<?xml version="1.0" ?>'
                    '<instance xmlns="http://docs.openstack.org/database/api/v1.0" name="xml_rack_instance" flavorRef="%s/flavors/1">'
                    '<databases>'
                    '<database name="sampledb" character_set="utf8" collate="utf8_general_ci" />'
                    '<database name="nextround" />'
                    '</databases>'
                    '<volume size="2" />'
                    '</instance>') % self.dbaas_url
        body = {'xml': XML_DATA, 'json': json.dumps(JSON_DATA)}
        self.http_call("create_instance", url, 'POST', body=body)

    def post_create_databases(self, database_name, instance_id):
        # create database on instance
        url = "%s/instances/%s/databases" % (self.dbaas_url, instance_id)
        JSON_DATA = {
            "databases": [
                    {
                    "name": "testingdb",
                    "character_set": "utf8",
                    "collate": "utf8_general_ci"
                },

                    {
                    "name": "sampledb"
                }
            ]
        }
        XML_DATA = ('<?xml version="1.0" ?>'
                    '<Databases xmlns="http://docs.openstack.org/database/api/v1.0">'
                    '<Database name="%s" character_set="utf8" collate="utf8_general_ci" />'
                    '<Database name="anotherexampledb" />'
                    '</Databases>') % database_name
        body = {'xml': XML_DATA, 'json': json.dumps(JSON_DATA)}
        self.http_call("create_databases", url, 'POST', body=body)

    def get_list_databases(self, instance_id):
        # list databases on instance
        url = "%s/instances/%s/databases" % (self.dbaas_url, instance_id)
        self.http_call("list_databases", url, 'GET')

    def delete_databases(self, database_name, instance_id):
        # delete databases on instance
        url = "%s/instances/%s/databases/%s" % (self.dbaas_url, instance_id, database_name)
        self.http_call("delete_databases", url, 'DELETE')

    def post_create_users(self, instance_id, user_name):
        # create user
        url = "%s/instances/%s/users" % (self.dbaas_url, instance_id)
        JSON_DATA = {
            "users": [
                    {
                    "name": "dbuser3",
                    "password": "password",
                    "database": "databaseA"
                },
                    {
                    "name": "dbuser4",
                    "password": "password",
                    "databases": [
                            {
                            "name": "databaseB"
                        },
                            {
                            "name": "databaseC"
                        }
                    ]
                }
            ]
        }
        XML_DATA = ('<?xml version="1.0" ?>'
                    '<users xmlns="http://docs.openstack.org/database/api/v1.0">'
                    '<user name="%s" password="password" database="databaseC"/>'
                    '<user name="userwith2dbs" password="password">'
                    '<databases>'
                    '<database name="databaseA"/>'
                    '<database name="databaseB"/>'
                    '</databases>'
                    '</user>'
                    '</users>') % user_name
        body = {'xml': XML_DATA, 'json': json.dumps(JSON_DATA)}
        self.http_call("create_users", url, 'POST', body=body)

    def get_list_users(self, instance_id):
        # list users on instance
        url = "%s/instances/%s/users" % (self.dbaas_url, instance_id)
        self.http_call("list_users", url, 'GET')

    def delete_users(self, instance_id, user_name):
        # delete user on instance
        url = "%s/instances/%s/users/%s" % (self.dbaas_url, instance_id, user_name)
        self.http_call("delete_users", url, 'DELETE')

    def post_enable_root_access(self, instance_id):
        # enable root access on instance
        url = "%s/instances/%s/root" % (self.dbaas_url, instance_id)
        self.http_call("enable_root_user", url, 'POST')

    def get_check_root_access(self, instance_id):
        # check root user access on instance
        url = "%s/instances/%s/root" % (self.dbaas_url, instance_id)
        self.http_call("check_root_user", url, 'GET')

    def get_list_instance_index(self):
        # list instances index call
        url = "%s/instances" % self.dbaas_url
        self.http_call("instances_index", url, 'GET')

    def get_list_instance_details(self):
        # list instances details call
        url = "%s/instances/detail" % self.dbaas_url
        self.http_call("instances_detail", url, 'GET')

    def get_instance_details(self, instance_id):
        # get instance details
        url = "%s/instances/%s" % (self.dbaas_url, instance_id)
        self.http_call("instance_status_detail", url, 'GET')

    def delete_instance(self, instance_id):
        # delete instance
        url = "%s/instances/%s" % (self.dbaas_url, instance_id)
        self.http_call("delete_instance", url, 'DELETE')

    def delete_other_instance(self, example_instances):
        # clean up other instance
        url = "%s/instances/%s" % (self.dbaas_url, example_instances[1])
        self.http_call("delete_instance", url, 'DELETE', output=False)

    def main(self):

        # Verify this is a clean environment to work on
        self.check_clean()
        self.get_versions()

        #requires auth
        self.get_version()
        self.get_flavors()
        self.get_flavor_details()
        self.get_flavor_by_id()

        self.post_create_instance()

        # this will be used later to make instance related calls
        example_instances = self.wait_for_instances()
        if len(example_instances) != 2:
            print("------------------------------------------------------------")
            print("------------------------------------------------------------")
            print("SOMETHING WENT WRONG CREATING THE INSTANCES FOR THE EXAMPLES")
            print("------------------------------------------------------------")
            print("------------------------------------------------------------")
            return 1

        instance_id = example_instances[0]
    #    instance_id = "c4a69fae-0aa0-4041-b0fc-f61cc03c01f6"
        database_name = "exampledb"
        user_name = "testuser"
        print "\nusing instance id(%s) for these calls\n" % instance_id

        self.post_create_databases(database_name, instance_id)
        self.get_list_databases(instance_id)
        self.delete_databases(database_name, instance_id)
        self.post_create_users(instance_id, user_name)
        self.get_list_users(instance_id)
        self.delete_users(instance_id, user_name)
        self.post_enable_root_access(instance_id)
        self.get_check_root_access(instance_id)
        self.get_list_instance_index()
        self.get_list_instance_details()
        self.get_instance_details(instance_id)
        self.delete_instance(instance_id)
        self.delete_other_instance(example_instances)


if __name__ == "__main__":
    print("RUNNING ARGS :  " + str(sys.argv))
    for arg in sys.argv[1:]:
        conf_file = os.path.expanduser(arg)
        print("Setting conf to " + conf_file)
        examples = ExampleGenerator(conf_file)
        examples.main()
