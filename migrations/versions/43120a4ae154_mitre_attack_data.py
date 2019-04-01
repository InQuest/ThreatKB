"""mitre attack data

Revision ID: 43120a4ae154
Revises: 650b0ad88d25
Create Date: 2019-03-30 11:43:37.921242

"""
import datetime
from alembic import op
import sqlalchemy as sa
from app.models import cfg_settings
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '43120a4ae154'
down_revision = '650b0ad88d25'
branch_labels = None
depends_on = None

techniques = ["T1156 - .bash_profile and .bashrc", "T1134 - Access Token Manipulation",
              "T1015 - Accessibility Features", "T1087 - Account Discovery", "T1098 - Account Manipulation",
              "T1182 - AppCert DLLs", "T1103 - AppInit DLLs", "T1155 - AppleScript",
              "T1017 - Application Deployment Software", "T1138 - Application Shimming",
              "T1010 - Application Window Discovery", "T1123 - Audio Capture", "T1131 - Authentication Package",
              "T1119 - Automated Collection", "T1020 - Automated Exfiltration", "T1139 - Bash History",
              "T1009 - Binary Padding", "T1197 - BITS Jobs", "T1067 - Bootkit", "T1217 - Browser Bookmark Discovery",
              "T1176 - Browser Extensions", "T1110 - Brute Force", "T1088 - Bypass User Account Control",
              "T1042 - Change Default File Association", "T1146 - Clear Command History", "T1115 - Clipboard Data",
              "T1191 - CMSTP", "T1116 - Code Signing", "T1059 - Command-Line Interface", "T1043 - Commonly Used Port",
              "T1092 - Communication Through Removable Media", "T1223 - Compiled HTML File",
              "T1109 - Component Firmware", "T1122 - Component Object Model Hijacking", "T1090 - Connection Proxy",
              "T1196 - Control Panel Items", "T1136 - Create Account", "T1003 - Credential Dumping",
              "T1081 - Credentials in Files", "T1214 - Credentials in Registry",
              "T1094 - Custom Command and Control Protocol", "T1024 - Custom Cryptographic Protocol",
              "T1002 - Data Compressed", "T1132 - Data Encoding", "T1022 - Data Encrypted",
              "T1213 - Data from Information Repositories", "T1005 - Data from Local System",
              "T1039 - Data from Network Shared Drive", "T1025 - Data from Removable Media", "T1001 - Data Obfuscation",
              "T1074 - Data Staged", "T1030 - Data Transfer Size Limits", "T1207 - DCShadow",
              "T1140 - Deobfuscate/Decode Files or Information", "T1089 - Disabling Security Tools",
              "T1175 - Distributed Component Object Model", "T1038 - DLL Search Order Hijacking",
              "T1073 - DLL Side-Loading", "T1172 - Domain Fronting", "T1189 - Drive-by Compromise",
              "T1157 - Dylib Hijacking", "T1173 - Dynamic Data Exchange", "T1114 - Email Collection",
              "T1106 - Execution through API", "T1129 - Execution through Module Load",
              "T1048 - Exfiltration Over Alternative Protocol", "T1041 - Exfiltration Over Command and Control Channel",
              "T1011 - Exfiltration Over Other Network Medium", "T1052 - Exfiltration Over Physical Medium",
              "T1190 - Exploit Public-Facing Application", "T1203 - Exploitation for Client Execution",
              "T1212 - Exploitation for Credential Access", "T1211 - Exploitation for Defense Evasion",
              "T1068 - Exploitation for Privilege Escalation", "T1210 - Exploitation of Remote Services",
              "T1133 - External Remote Services", "T1181 - Extra Window Memory Injection", "T1008 - Fallback Channels",
              "T1083 - File and Directory Discovery", "T1107 - File Deletion", "T1222 - File Permissions Modification",
              "T1006 - File System Logical Offsets", "T1044 - File System Permissions Weakness",
              "T1187 - Forced Authentication", "T1144 - Gatekeeper Bypass", "T1061 - Graphical User Interface",
              "T1200 - Hardware Additions", "T1158 - Hidden Files and Directories", "T1147 - Hidden Users",
              "T1143 - Hidden Window", "T1148 - HISTCONTROL", "T1179 - Hooking", "T1062 - Hypervisor",
              "T1183 - Image File Execution Options Injection", "T1054 - Indicator Blocking",
              "T1066 - Indicator Removal from Tools", "T1070 - Indicator Removal on Host",
              "T1202 - Indirect Command Execution", "T1056 - Input Capture", "T1141 - Input Prompt",
              "T1130 - Install Root Certificate", "T1118 - InstallUtil", "T1208 - Kerberoasting",
              "T1215 - Kernel Modules and Extensions", "T1142 - Keychain", "T1159 - Launch Agent",
              "T1160 - Launch Daemon", "T1152 - Launchctl", "T1161 - LC_LOAD_DYLIB Addition",
              "T1149 - LC_MAIN Hijacking", "T1171 - LLMNR/NBT-NS Poisoning", "T1168 - Local Job Scheduling",
              "T1162 - Login Item", "T1037 - Logon Scripts", "T1177 - LSASS Driver", "T1185 - Man in the Browser",
              "T1036 - Masquerading", "T1031 - Modify Existing Service", "T1112 - Modify Registry", "T1170 - Mshta",
              "T1188 - Multi-hop Proxy", "T1104 - Multi-Stage Channels", "T1026 - Multiband Communication",
              "T1079 - Multilayer Encryption", "T1128 - Netsh Helper DLL", "T1046 - Network Service Scanning",
              "T1126 - Network Share Connection Removal", "T1135 - Network Share Discovery", "T1040 - Network Sniffing",
              "T1050 - New Service", "T1096 - NTFS File Attributes", "T1027 - Obfuscated Files or Information",
              "T1137 - Office Application Startup", "T1075 - Pass the Hash", "T1097 - Pass the Ticket",
              "T1174 - Password Filter DLL", "T1201 - Password Policy Discovery", "T1034 - Path Interception",
              "T1120 - Peripheral Device Discovery", "T1069 - Permission Groups Discovery",
              "T1150 - Plist Modification", "T1205 - Port Knocking", "T1013 - Port Monitors", "T1086 - PowerShell",
              "T1145 - Private Keys", "T1057 - Process Discovery", "T1186 - Process Doppelgnging",
              "T1093 - Process Hollowing", "T1055 - Process Injection", "T1012 - Query Registry", "T1163 - Rc.common",
              "T1164 - Re-opened Applications", "T1108 - Redundant Access",
              "T1060 - Registry Run Keys / Startup Folder", "T1121 - Regsvcs/Regasm", "T1117 - Regsvr32",
              "T1219 - Remote Access Tools", "T1076 - Remote Desktop Protocol", "T1105 - Remote File Copy",
              "T1021 - Remote Services", "T1018 - Remote System Discovery",
              "T1091 - Replication Through Removable Media", "T1014 - Rootkit", "T1085 - Rundll32",
              "T1053 - Scheduled Task", "T1029 - Scheduled Transfer", "T1113 - Screen Capture", "T1180 - Screensaver",
              "T1064 - Scripting", "T1063 - Security Software Discovery", "T1101 - Security Support Provider",
              "T1167 - Securityd Memory", "T1035 - Service Execution", "T1058 - Service Registry Permissions Weakness",
              "T1166 - Setuid and Setgid", "T1051 - Shared Webroot", "T1023 - Shortcut Modification",
              "T1178 - SID-History Injection", "T1218 - Signed Binary Proxy Execution",
              "T1216 - Signed Script Proxy Execution", "T1198 - SIP and Trust Provider Hijacking",
              "T1045 - Software Packing", "T1153 - Source", "T1151 - Space after Filename",
              "T1193 - Spearphishing Attachment", "T1192 - Spearphishing Link", "T1194 - Spearphishing via Service",
              "T1184 - SSH Hijacking", "T1071 - Standard Application Layer Protocol",
              "T1032 - Standard Cryptographic Protocol", "T1095 - Standard Non-Application Layer Protocol",
              "T1165 - Startup Items", "T1169 - Sudo", "T1206 - Sudo Caching", "T1195 - Supply Chain Compromise",
              "T1019 - System Firmware - ate as the software interface between the operating system and hardware of a computer.",
              "T1082 - System Information Discovery", "T1016 - System Network Configuration Discovery",
              "T1049 - System Network Connections Discovery", "T1033 - System Owner/User Discovery",
              "T1007 - System Service Discovery", "T1124 - System Time Discovery", "T1080 - Taint Shared Content",
              "T1221 - Template Injection", "T1072 - Third-party Software", "T1209 - Time Providers",
              "T1099 - Timestomp", "T1154 - Trap", "T1127 - Trusted Developer Utilities",
              "T1199 - Trusted Relationship", "T1111 - Two-Factor Authentication Interception",
              "T1065 - Uncommonly Used Port", "T1204 - User Execution", "T1078 - Valid Accounts",
              "T1125 - Video Capture", "T1102 - Web Service", "T1100 - Web Shell", "T1077 - Windows Admin Shares",
              "T1047 - Windows Management Instrumentation",
              "T1084 - Windows Management Instrumentation Event Subscription", "T1028 - Windows Remote Management",
              "T1004 - Winlogon Helper DLL", "T1220 - XSL Script Processing"]
tactics = ["TA0001 - Initial Access", "TA0002 - Execution", "TA0003 - Persistence", "TA0004 - Privilege Escalation",
           "TA0005 - Defense Evasion", "TA0006 - Credential Access", "TA0007 - Discovery", "TA0008 - Lateral Movement",
           "TA0009 - Collection", "TA0010 - Exfiltration", "TA0011 - Command and Control"]


def upgrade():
    op.add_column('yara_rules', sa.Column('_mitre_tactics', sa.String(256), nullable=True))
    op.add_column('yara_rules', sa.Column('_mitre_techniques', sa.String(256), nullable=True))
    op.create_index(u'ix_yara_rules__mitre_tactics', 'yara_rules', ['_mitre_tactics'], unique=False)
    op.create_index(u'ix_yara_rules__mitre_techniques', 'yara_rules', ['_mitre_techniques'], unique=False)

    date_created = datetime.datetime.now().isoformat()
    date_modified = datetime.datetime.now().isoformat()

    op.bulk_insert(
        cfg_settings.Cfg_settings.__table__,
        [
            {
                "key": "MITRE_TECHNIQUES",
                "value": ",".join(techniques),
                "public": True,
                "date_created": date_created,
                "date_modified": date_modified,
                "description": "The MITRE ATT&CK techniques."
            },
            {
                "key": "MITRE_TACTICS",
                "value": ",".join(tactics),
                "public": True,
                "date_created": date_created,
                "date_modified": date_modified,
                "description": "The MITRE ATT&CK tactices."
            }
        ]
    )


def downgrade():
    op.drop_index(u'ix_yara_rules__mitre_techniques', table_name='yara_rules')
    op.drop_index(u'ix_yara_rules__mitre_tactics', table_name='yara_rules')
    op.drop_column('yara_rules', '_mitre_techniques')
    op.drop_column('yara_rules', '_mitre_tactics')
    keys = ["MITRE_TECHNIQUES", "MITRE_TACTICS"]
    for key in keys:
        op.execute("""DELETE from cfg_settings where `key`='%s';""" % (key))
