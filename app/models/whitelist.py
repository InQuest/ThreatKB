from app import db, cache
from app.models.cfg_settings import Cfg_settings
from app.models.cfg_states import Cfg_states, get_cfg_states
import distutils
import re
import time
from ipaddr import IPAddress, IPNetwork


class WhitelistException(Exception):
    pass


@cache.memoize(timeout=300)
def get_whitelist_cache():
    return Whitelist.query.all()


class Whitelist(db.Model):
    __tablename__ = "whitelist"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    whitelist_artifact = db.Column(db.String(2048))
    notes = db.Column(db.String(2048))

    created_by_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=True)
    created_by_user = db.relationship('KBUser', foreign_keys=created_by_user_id,
                                      primaryjoin="KBUser.id==Whitelist.created_by_user_id")
    modified_by_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=True)
    modified_by_user = db.relationship('KBUser', foreign_keys=modified_by_user_id,
                                       primaryjoin="KBUser.id==Whitelist.modified_by_user_id")
    created_time = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    modified_time = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())

    def to_dict(self):
        return dict(
            id=self.id,
            whitelist_artifact=self.whitelist_artifact,
            notes=self.notes,
            created_time=self.created_time.isoformat(),
            modified_time=self.modified_time.isoformat()
        )

    @staticmethod
    def hits_whitelist(indicator, state):
        whitelist_enabled = Cfg_settings.get_setting("ENABLE_IP_WHITELIST_CHECK_ON_SAVE")
        whitelist_states = Cfg_settings.get_setting("WHITELIST_STATES")

        if not whitelist_enabled or not distutils.util.strtobool(whitelist_enabled) or not whitelist_states:
            return True

        states = []

        for s in whitelist_states.split(","):
            if s in get_cfg_states():
                states.append(s)

        if state in states:
            new_ip = indicator

            abort_import = False

            whitelists = get_whitelist_cache()

            for whitelist in whitelists:
                wa = str(whitelist.whitelist_artifact)

                try:
                    if str(IPAddress(new_ip)) == str(IPAddress(wa)):
                        abort_import = True
                        break
                except ValueError:
                    pass

                try:
                    if IPAddress(new_ip) in IPNetwork(wa):
                        abort_import = True
                        break
                except ValueError:
                    pass

                try:
                    regex = re.compile(wa)
                    result = regex.search(new_ip)
                except:
                    result = False

                if result:
                    abort_import = True
                    break

            if abort_import:
                return True

        return False
