from app import db
import tempfile
import subprocess
import re


class Scripts(db.Model):
    __tablename__ = "scripts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(128), nullable=True)
    interpreter = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(60000), nullable=True)
    match_regex = db.Column(db.String(4096), nullable=True)
    date_created = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime(timezone=True), default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    created_user_id = db.Column(db.Integer, db.ForeignKey('kb_users.id'), nullable=False)
    created_user = db.relationship('KBUser', foreign_keys=created_user_id,
                                   primaryjoin="KBUser.id==Scripts.created_user_id")

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            description=self.description,
            code=self.code,
            interpreter=self.interpreter,
            match_regex=self.match_regex,
            date_created=self.date_created.isoformat(),
            date_modified=self.date_modified.isoformat(),
            created_user=self.created_user.to_dict(),
        )

    def run_script(self, arguments, highlight_lines_matching=None, timeout=10):
        temp_script = "%s/%s" % (tempfile.gettempdir(), re.sub("[^A-Za-z0-9_\.]", "", self.name))
        with open(temp_script, "w") as s:
            s.write(self.code)

        command = [self.interpreter, temp_script]
        command.extend(arguments)
        # results = envoy.run(" ".join(command), timeout=timeout)
        proc = subprocess.Popen(" ".join(command), stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        proc.wait()
        stdout, stderr = proc.communicate()

        results = {"stdout": stdout, "stderr": stderr, "retcode": proc.returncode,
                   "command": " ".join(command)}

        try:
            if self.match_regex:
                results["stdout"] = re.sub("(" + self.match_regex + ")", "<mark>\\1</mark>", results["stdout"])
        except:
            pass

        try:
            if highlight_lines_matching:
                results["stdout"] = re.sub("(" + highlight_lines_matching + ")", "<mark>\\1</mark>", results["stdout"])
        except:
            pass

        return results

    def __repr__(self):
        return '<Script %r>' % (self.id)
