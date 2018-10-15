import glob
import os
from shutil import copyfile
import json
from configparser import ConfigParser
class ZeroCenterDH(object):
    """
    Doc
    """
    def __init__(self):
        self.appext = 'app'
        self.zmdext = 'zmd'
        self.basefolder = 'usr/share/zero-center/'
        self.appfolder = self.basefolder + 'applications'
        self.zmdfolder = self.basefolder + 'zmds'

    def install_files(self, pkg, folder):
        """
        Doc
        """
        list_apps = glob.glob(os.path.join(folder.strip('/'), '*.' + self.appext))
        list_zmds = glob.glob(os.path.join(folder.strip('/'), '*.' + self.zmdext))
        if list_apps:
            dest_app = os.path.join('debian', pkg, self.appfolder)
            self.exists_or_create(dest_app)
            for app in list_apps:
                filename = os.path.basename(app)
                copyfile(app, os.path.join(dest_app, filename))

        if list_zmds:
            dest_zmd = os.path.join('debian', pkg, self.zmdfolder)
            self.exists_or_create(dest_zmd)
            for zmd in list_zmds:
                filename = os.path.basename(zmd)
                final_path = os.path.join(dest_zmd, filename)
                copyfile(zmd, final_path)
                os.chmod(final_path, 0o755)

        return True


    def write_pkexec_files(self, pkg, folder):
        """
        Doc
        """
        pkexec_description = []
        if os.path.exists('debian/{pkg}.pkexec'.format(pkg=pkg)):
            with open('debian/{pkg}.pkexec'.format(pkg=pkg)) as file_descriptor:
                pkexec_description = json.load(file_descriptor)

        list_apps = glob.glob(os.path.join(folder.strip('/'), '*.'+self.appext))
        if list_apps:
            for app in list_apps:
                app_description = ConfigParser()
                with open(app) as file_descriptor:
                    file_content = '[root]\n'+ file_descriptor.read()
                    app_description.read_string(file_content)
                if app_description.has_option('root', 'Using'):
                    if app_description.get('root', 'Using') == 'pkexec':
                        pkexec_process = {}
                        pkexec_process['prefix'] = 'net.lliurex.zero-center.' + app_description.get('root','Name')
                        pkexec_process['cmd'] = os.path.join('/',self.zmdfolder, app_description.get('root','ScriptPath'))
                        pkexec_process['nameaction'] = 'launcher'
                        pkexec_process['icon'] = app_description.get('root', 'Icon')
                        pkexec_process['default_auth'] = {'any':'no', 'inactive':'no', 'active': 'no'}
                        pkexec_process['auths'] = []
                        if app_description.has_option('root', 'Groups'):
                            auth = {'type':'group','members':[], 'any': 'yes', 'inactive':'yes', 'active':'yes' }
                            for group in list(filter(None,app_description.get('root','Groups').split(';'))):
                                auth['members'].append(group)
                            if auth['members']:
                                pkexec_process['auths'].append(auth)

                        if app_description.has_option('root', 'Users'):
                            auth = {'type':'users','members':[], 'any': 'yes', 'inactive':'yes', 'active':'yes' }
                            for group in list(filter(None,app_description.get('root','Users').split(';'))):
                                auth['members'].append(group)
                            if auth['members']:
                                pkexec_process['auths'].append(auth)

                        if not pkexec_process['auths']:
                            del(pkexec_process['auths'])
                        if not pkexec_process['prefix'] in [x['prefix'] for x in pkexec_description]:
                            pkexec_description.append(pkexec_process)

        with open('debian/{pkg}.pkexec'.format(pkg=pkg), 'w') as file_descriptor:
            json.dump(pkexec_description, file_descriptor, indent=4)




    def exists_or_create(self, folder):
        """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
        """
        if os.path.isdir(folder):
            pass
        elif os.path.isfile(folder):
            raise OSError("a file with the same name as the desired " \
                        "dir, '%s', already exists." % folder)
        else:
            head, tail = os.path.split(folder)
            if head and not os.path.isdir(head):
                self.exists_or_create(head)
            #print "_mkdir %s" % repr(folder)
            if tail:
                os.mkdir(folder)
