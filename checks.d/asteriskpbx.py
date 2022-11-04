#
# requires pyst2 for Asterisk Manager Interface
# https://github.com/rdegges/pyst2
#
# requires re for regular expression matching on asterisk output
#
#

import asterisk.manager
import re
from checks import AgentCheck

###Internal, Inbound, Outbound Calls Classes
class Channel:
  def __init__(self,Channel,Context,Extension,Priority,State,Application,Data,CallerId,Duration,AccountCode,PeerAccount,BridgedTo):
    self.Channel        = Channel
    self.Context        = Context
    self.Extension      = Extension
    self.Priority       = Priority
    self.State          = State
    self.Application    = Application
    self.Data           = Data
    self.CallerId       = CallerId
    self.Duration       = Duration
    self.AccountCode    = AccountCode
    self.PeerAccount    = PeerAccount
    self.BridgedTo      = BridgedTo

class Call:
  def __init__(self,Caller,CallerChannel,Called,CalledChannel,BridgedChannel,CallType):
    self.Caller         = Caller
    self.CallerChannel  = CallerChannel
    self.Called         = Called
    self.CalledChannel  = CalledChannel
    self.BridgedChannel = BridgedChannel
    self.CallType       = CallType

class AsteriskCheck(AgentCheck):

    def check(self, instance):

        if 'host' not in instance:
            instance['host'] = 'localhost'
        if 'extension_length' not in instance:
            self.log.error('extension_length not defined, skipping')
            return
        if 'manager_user' not in instance:
            self.log.error('manager_user not defined, skipping')
            return
        if 'manager_secret' not in instance:
            self.log.error('manager_secret not defined, skipping')
            return
            

######  Connect
        mgr = asterisk.manager.Manager()
        try:
            if 'port' in instance:
                mgr.connect(instance['host'],instance['port'])
            else:
                mgr.connect(instance['host'])
            mgr.login(instance['manager_user'],instance['manager_secret'])
        except asterisk.manager.ManagerSocketException as e:
            self.log.error('Error connecting to Asterisk Manager Interface')
            mgr.close()
            return
        except asterisk.manager.ManagerAuthException as e:
            self.log.error('Error Logging in to Asterisk Manager Interface')
            mgr.close()
            return

##### Call Volume
        self.log.error("asterisk check starting call volume")
        try:
            call_volume = mgr.command('core show calls')

            current_call_vol = call_volume.data.split('\n')
            procesed_call_vol = current_call_vol[1].replace('Output: ', '')
            procesed_call_vol = procesed_call_vol.replace(' calls processed','')
            current_call_vol = current_call_vol[0].replace('active call','')
            current_call_vol = current_call_vol.replace('s','')
            current_call_vol = current_call_vol.replace(' ','')
            current_call_vol = current_call_vol.replace('Output:','')

            self.gauge('asterisk.callsprocesed',procesed_call_vol)
            self.gauge('asterisk.callvolume',current_call_vol)
        
        except asterisk.manager.ManagerSocketException as e:
            self.log.info("Error connecting to the manager: %s" % e.strerror)
    
        except asterisk.manager.ManagerAuthException as e:
            self.log.info("Error logging in to the manager: %s" % e.strerror)
    
        except asterisk.manager.ManagerException as e:
       	    self.log.info("Error: %s" % e.strerror)
##### Internal, Inbound Outbound Calls
        self.log.error("asterisk check starting internal call volume")

        extensionLength = instance['extension_length']

        current_channels = mgr.command('core show channels verbose')
        current_channels = current_channels.data.split('\n')
        current_channels[0] = None
        current_channels_size = len(current_channels)
        current_channels[current_channels_size-1] = None
        current_channels[current_channels_size-2] = None
        current_channels[current_channels_size-3] = None
        current_channels[current_channels_size-4] = None
        current_channels[current_channels_size-5] = None

        currentChannelsArray = []
        currentCalls = []

        for chan in current_channels:
            if chan != None:
                channel     = re.sub(' +',' ',chan[0:21]).lstrip(' ').rstrip(' ')
                context     = re.sub(' +',' ',chan[21:42]).lstrip(' ').rstrip(' ')
                extension   = re.sub(' +',' ',chan[42:59]).lstrip(' ').rstrip(' ')
                priority    = re.sub(' +',' ',chan[59:64]).lstrip(' ').rstrip(' ')
                state       = re.sub(' +',' ',chan[64:72]).lstrip(' ').rstrip(' ')
                application = re.sub(' +',' ',chan[72:85]).lstrip(' ').rstrip(' ')
                data        = re.sub(' +',' ',chan[85:111]).lstrip(' ').rstrip(' ')
                callerid    = re.sub(' +',' ',chan[111:127]).lstrip(' ').rstrip(' ')
                duration    = re.sub(' +',' ',chan[127:136]).lstrip(' ').rstrip(' ')
                accountcode = re.sub(' +',' ',chan[136:148]).lstrip(' ').rstrip(' ')
                peeraccount = re.sub(' +',' ',chan[148:160]).lstrip(' ').rstrip(' ')
                bridgedto   = re.sub(' +',' ',chan[160:181]).lstrip(' ').rstrip(' ')
                currentChannel = Channel(channel,context,extension,priority,state,application,data,callerid,duration,accountcode,peeraccount,bridgedto)
                currentChannelsArray.append(currentChannel)

        internalCalls = 0
        outboundCalls = 0
        inboundCalls  = 0
        conferenceCalls = 0

        for currentChannel in currentChannelsArray:
            caller = "N/A"
            called = "N/A"
            callType = "N/A"

            if "Dial" == currentChannel.Application or "Queue" == currentChannel.Application:
                currentCall = Call("N/A","N/A","N/A","N/A","N/A","N/A")
                currentCall.Caller = currentChannel.CallerId
                currentCall.CallerChannel = currentChannel.Channel
                currentCall.BridgedChannel = currentChannel.BridgedTo
                currentCalls.append(currentCall)

            if "ConfBridge" == currentChannel.Application:
                currentCall = Call("N/A","N/A","N/A","N/A","N/A","N/A")
                currentCall.Caller = currentChannel.CallerId
                currentCall.CallerChannel = currentChannel.Channel
                calledConference = currentChannel.Data.split(',')
                calledConference = calledConference[0]
                currentCall.Called = calledConference
                currentCall.CalledChannel = currentChannel.Channel
                conferenceCalls = conferenceCalls +1

        for currentCall in currentCalls:
            caller = "N/A"
            called = "N/A"
            callType = "N/A"
            for currentChannel in currentChannelsArray:
                if "None" not in currentChannel.BridgedTo:
                    if currentCall.BridgedChannel == currentChannel.Channel:
                        currentCall.Called = currentChannel.CallerId
                        currentCall.CalledChannel = currentChannel.Channel

        for currentCall in currentCalls:
            if len(currentCall.Caller) <= extensionLength and len(currentCall.Called) <= extensionLength:
                currentCall.CallType = "Internal"
                internalCalls = internalCalls +1
            if len(currentCall.Caller) > extensionLength and len(currentCall.Called) <= extensionLength:
                currentCall.CallType = "Inbound"
                inboundCalls = inboundCalls + 1
            if len(currentCall.Caller) <= extensionLength and len(currentCall.Called) > extensionLength:
                currentCall.CallType = "Outbound"
                outboundCalls = outboundCalls + 1

        self.gauge('asterisk.calls.internal',internalCalls)
        self.gauge('asterisk.calls.inbound',inboundCalls)
        self.gauge('asterisk.calls.outbound',outboundCalls)
        self.gauge('asterisk.calls.conference',conferenceCalls)

##### PJSIP Endpoints
        self.log.error("asterisk check starting PJSIP endpoints")

        sip_result = mgr.command('pjsip show endpoints')

        if "No such command" not in sip_result.data:
            sip_results = sip_result.data.split('\n')

            siptotals = sip_results[len(sip_results)-3]

            siptotal = re.findall(r'Objects found: ([0-9]+)',siptotals)[0]
            monitored_peers_online = sip_result.data.count(" Avail ")
            monitored_peers_offline = sip_result.data.count(" UnAvail ")
	         
            self.gauge('asterisk.pjsip.peers',siptotal)
            self.gauge('asterisk.pjsip.monitored.online',monitored_peers_online)
            self.gauge('asterisk.pjsip.monitored.offline',monitored_peers_offline)



##### Asterisk Uptime
        self.log.error("asterisk check starting uptime")

        uptime_result = mgr.command('core show uptime')
        
        uptime_results = uptime_result.data.split('\n')
        
        system_total_line = uptime_results[0]
        asterisk_total_line = uptime_results[1]
        
        system_uptime_days = 0
        system_uptime_hours = 0
        system_uptime_minutes = 0
        system_uptime_seconds = 0
        
        system_uptime_days = 0
        system_uptime_hours = 0
        system_uptime_minutes = 0
        system_uptime_seconds = 0

        if "day" in system_total_line:
            system_uptime_days = re.findall(r'([0-9]+) day',system_total_line)[0]
        if "hour" in system_total_line:
            system_uptime_hours = re.findall(r'([0-9]+) hour',system_total_line)[0]
        if "minute" in system_total_line:
            system_uptime_minutes = re.findall(r'([0-9]+) minute',system_total_line)[0]
        if "second" in system_total_line:
            system_uptime_seconds = re.findall(r'([0-9]+) second',system_total_line)[0]

        system_uptime = ( int(system_uptime_days) * 86400) +  ( int(system_uptime_hours) * 3600) + ( int(system_uptime_minutes) * 60) + int(system_uptime_seconds)
        
        asterisk_last_reload_days = 0
        asterisk_last_reload_hours = 0
        asterisk_last_reload_minutes = 0
        asterisk_last_reload_seconds = 0
        
        if "day" in asterisk_total_line:
            asterisk_last_reload_days = re.findall(r'([0-9]+) day',asterisk_total_line)[0]
        if "hour" in asterisk_total_line:
            asterisk_last_reload_hours = re.findall(r'([0-9]+) hour',asterisk_total_line)[0]
        if "minute" in asterisk_total_line:
            asterisk_last_reload_minutes = re.findall(r'([0-9]+) minute',asterisk_total_line)[0]
        if "second" in asterisk_total_line:
            asterisk_last_reload_seconds = re.findall(r' ([0-9]+) second',asterisk_total_line)[0]

        asterisk_last_reload = ( int(asterisk_last_reload_days) * 86400) + ( int(asterisk_last_reload_hours) * 3600) + ( int(asterisk_last_reload_minutes) * 60) + int(asterisk_last_reload_seconds)

        self.gauge('asterisk.system.uptime',system_uptime)
        self.gauge('asterisk.last.reload',asterisk_last_reload)
        
##### Close connection
        self.log.error("asterisk closing mgr connection")

        mgr.close()
