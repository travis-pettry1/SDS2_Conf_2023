from pickle import NONE
import SelectionDialog as SD
from materialfile import MaterialFile
import os
import os.path
import time
import subprocess
import job
import model
from xml.dom.minidom import parseString, getDOMImplementation
from Commands import *
from param import ResponseNotOK, NonBlockingWarning
from job import JobName
from sds2 import UserSettings

class Child(object):
    def __init__(self, pid):
        self.ipipe = self.opipe = None
        while(True):
            try:
                if not self.ipipe:
                    self.ipipe = open(r'\\.\PIPE\SDS2HYBRID%iO' % pid, 'r+b', buffering=0)
                if not self.opipe:
                    self.opipe = open(r'\\.\PIPE\SDS2HYBRID%iI' % pid, 'r+b', buffering=0)
                break
            except:
                time.sleep(0.1)

    def Send(self, message):
        message_bytes = message.encode('utf-8')
        header = str(len(message_bytes)).zfill(10)
        header_bytes = header.encode('utf-8')
    
        # Write the header and message bytes to the pipe
        self.opipe.write(header_bytes)
        self.opipe.write(message_bytes)
        self.opipe.seek(0)

    def Recv(self):
        self.ipipe.seek(0)
        header = self.ipipe.read(10)
        toread = int(header)
        dat = self.ipipe.read(toread)
        self.ipipe.seek(0)
        return dat

    def Close(self):
        self.ipipe.close()
        self.opipe.close()


def CreateSelectionMessage(selection, sequence):
    impl = getDOMImplementation()
    doc = impl.createDocument(None, "selection", None)
    top = doc.documentElement
    top.setAttribute("sequence", str(sequence))
    for i in selection:
        item = doc.createElement("item")
        item.setAttribute("member", str(i._as_tuple[0]))
        item.setAttribute("end", str(i._as_tuple[1]))
        item.setAttribute("material", str(i._as_tuple[2]))
        item.setAttribute("hole", str(i._as_tuple[3]))
        item.setAttribute("bolt", str(i._as_tuple[4]))
        item.setAttribute("weld", str(i._as_tuple[5]))
        top.appendChild(item)
    return doc.toprettyxml()
    
def CreateListMessage(selection, sequence):
    impl = getDOMImplementation()
    doc = impl.createDocument(None, "list", None)
    top = doc.documentElement
    top.setAttribute("sequence", str(sequence))
    for i in selection:
        item = doc.createElement("item")
        item.setAttribute("listElement", str(i))
        top.appendChild(item)
    return doc.toprettyxml()

def CreateMessage(item, returnType, sequence):
    impl = getDOMImplementation()
    doc = impl.createDocument(None, "selectedItem", None)
    top = doc.documentElement
    top.setAttribute("sequence", str(sequence))    
    xmlItem = doc.createElement("item")
    xmlItem.setAttribute("value", str(item))
    xmlItem.setAttribute("type", returnType)
    top.appendChild(xmlItem)
    return doc.toprettyxml()

def ParseCommand(command):
    doc = parseString(command)
    top = doc.documentElement
    if top.nodeName == "command":
        attr = dict(top.attributes.items())
        val = ""
        if top.firstChild:
            val = str(top.firstChild.nodeValue)
        return "command", str(attr["type"]), attr["sequence"], val


Prompts = [
"",
"Locate Member:",
"Locate Members:",
"Locate Member End:",
"Locate Member Ends:",
"Locate Material:",
"Locate Materials:",
"Locate Bolt:",
"Locate Bolts:",
"Locate Weld:",
"Locate Welds:",
"Locate Material, bolt, or weld:",
"Locate Material, bolts, and welds:",
"Locate Hole:",
"Locate Holes:"
]

class Demo(Command):
    def __init__(self):
        Command.__init__(
            self,
            operations=OperationClass.Member,
            listings=Listing.All,
            icons=IconSet((Icon(os.path.join(os.path.dirname(__file__),'Demo_small.png')),
                               Icon(os.path.join(os.path.dirname(__file__),'Demo_large.png')))),
            long_description="Demo",
            command_text="""Demo""",
            alt_text="""Demo""",
            documentation="""""",
            clone=False,
            stations=(Station.Frame | Station.FrameReview | Station.FrameBim | Station.FrameErector | Station.FrameErectorPlus 
					  | Station.FrameApproval | Station.FrameFabricator | Station.FrameModelstn | Station.FrameDraftstn 
					  | Station.FrameLite | Station.FrameErectorPlus),
            type=CommandType.Command
        )

    def Invoke(self, args):
        directory = os.path.dirname(__file__)
        exe = os.path.join(directory, "app/DemoApp.exe") 
        args = ["theme:" + str(int(UserSettings.GetUserInterfaceAppearance()))]
        childProcess = subprocess.Popen([exe, *args])
        separator = "__!__"

        pipe = Child(childProcess.pid)

        prompts = Prompts
        while(True):
            model.Deselect(model.GetSelection())
            try:
	            message = pipe.Recv();
            except:
                break
            messageType, name, sequence, text = ParseCommand(message)
			
            selected_sheets = None
            sel = None
            selectedItem = None
			
            if name == "0" or messageType == "finished":
                pipe.Close()
                break
            elif name == "1":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateSingle, filter_fn=model.IsMember)
            elif name == "2":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateMultiple, filter_fn=model.IsMember)
            elif name == "3":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateSingle, filter_fn=model.IsEnd)	
            elif name == "4":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateMultiple, filter_fn=model.IsEnd)
            elif name == "5":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateSingle, filter_fn=model.IsMaterial)
            elif name == "6":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateMultiple, filter_fn=model.IsMaterial)
            elif name == "7":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateSingle, filter_fn=model.IsBolt)
            elif name == "8":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateMultiple, filter_fn=model.IsBolt)
            elif name == "9":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateSingle, filter_fn=model.IsWeld)
            elif name == "10":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateMultiple, filter_fn=model.IsWeld)
            elif name == "11":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateSingle, filter_fn=lambda m: model.IsWeld(m) or model.IsMaterial(m) or model.IsBolt(m))
            elif name == "12":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateMultiple, filter_fn=lambda m: model.IsWeld(m) or model.IsMaterial(m) or model.IsBolt(m))
            elif name == "13":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateSingle, filter_fn=model.IsHole)
            elif name == "14":
                sel = model.PreOrPostSelection(prompt=prompts[int(name)], location_fn=model.LocateMultiple, filter_fn=model.IsHole)				
            elif name == "15":
                prompts = [text]*15
                continue #no reply for this.
            elif name == "16":
                parts = text.split(separator)
                ok, selected_sheets = SD.RunCustomSelectionDialogForManyItems(parts[0], parts[1].split(","), [] )
            elif name == "17":
                NonBlockingWarning(text)
                continue
            elif name == "18":
                selectedItem = None
                parts = text.split(separator)
                returnType = parts[0]
                                
                if len(parts) > 2:
                    filters = parts[2].split(",")
                if len(parts) > 3:
                    exclude = parts[3].split(",")
                    
                mask = []
                
                if filters is not None:
                    mask = self.createProfileList(filters)
                       
                shapes = []
                shapesToExclude = []                

                if exclude is not None:
                    shapesToExcludeTemp = self.createProfileList(exclude)
                    shapesToExclude = [str(s) for s in shapesToExcludeTemp]
                    
                for s in MaterialFile():
                    if s.type() not in shapesToExclude:
                        shapes.append(s)                    

                ok, selectedItem = SD.RunMaterialFileSelectionDialog( title=parts[1], shapes=shapes, mask=mask, )
                           
                

            if selected_sheets is not None:
                message = CreateListMessage(selected_sheets, sequence);
            elif sel is not None:
                code,sel = sel
                message = CreateSelectionMessage(sel, sequence)
            elif selectedItem is not None:
                message = CreateMessage(selectedItem, returnType, sequence)
            else:
                continue
            
            try:
                pipe.Send(message)
            except:
                break
            prompts = Prompts
            
    def createProfileList(self, list):
        result = []
        for item in list:
            if item == "2" or item == "1":
                result.append(model.WideFlange)
            if item == "3" or item == "1":
                result.append(model.Channel)
            if item == "4" or item == "1":
                result.append(model.Angle)
            if item == "5" or item == "1":
                result.append(model.WTee)
            if item == "6" or item == "1":
                result.append(model.Pipe)
            if item == "7" or item == "1":
                result.append(model.HSSTS)
            if item == "8" or item == "1":
                result.append(model.WeldedPlateSection)
            if item == "9" or item == "1":
                result.append(model.WeldedBoxSection)
            if item == "10" or item == "1":
                result.append(model.JoistMaterial)
            if item == "11" or item == "1":
                result.append(model.BeadedFlatSteel)
            if item == "12" or item == "1":
                result.append(model.ColdFormedChannel)
            if item == "13" or item == "1":
                result.append(model.ColdFormedZ)
            if item == "14" or item == "1":
                result.append(model.SSection)
            if item == "15" or item == "1":
                result.append(model.STeeSection)
            if item == "16" or item == "1":
                result.append(model.RoundBar)
            if item == "17" or item == "1":
                result.append(model.Clevis)
            if item == "18" or item == "1":
                result.append(model.Turnbuckle)
            if item == "19" or item == "1":
                result.append(model.CraneRail)
            if item == "20" or item == "1":
                result.append(model.Cruciform)                
        return result


