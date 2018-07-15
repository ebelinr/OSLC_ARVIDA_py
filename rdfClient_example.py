try:
    #python2
    import httplib as h
    import urllib as u
except ImportError:
    #python3
    import http.client as h
    import urllib.parse as u

from base64 import b64encode
import codecs

import inspect

import datetime, os, sys, time
from time import sleep as sleepingTime
import rdflib
import logging
from rdflib import ConjunctiveGraph, URIRef, Literal, Namespace, RDF
from rdflib.namespace import DC, DCTERMS, RDF, RDFS, XSD
import pprint
import numpy as np

logging.basicConfig()
#The following namespaces are available by directly importing from rdflib:
# RDF
# RDFS
# OWL
# XSD
# FOAF
# SKOS
# DOAP
# DC
# DCTERMS
# VOID

OSLC = Namespace("http://pen-services.net/ns/core#");
OSLC_DATA = Namespace("http://open-services.net/ns/servicemanagement/1.0/");
SPATIAL = Namespace("http://vocab.arvida.de/2015/06/spatial/vocab#");
SCENE = Namespace("http://vocab.arvida.de/2015/06/scene/vocab#");
SCENEGRAPH = Namespace("http://vocab.arvida.de/2015/06/scenegraph/vocab#");
MATHS = Namespace("http://vocab.arvida.de/2015/06/maths/vocab#");
SYSLM = Namespace("http://localhost.vocab.syslm.de/#");

# Calculates rotation matrix to euler angles
def rotationMatrixToEulerAngles(R):
    logging.debug("Hand rotationMatrixToEulerAngles("+str(R)+") start")
    sy = math.sqrt(R[0][0] * R[0][0] +  R[1][0] * R[1][0])
 
    singular = sy < 1e-6

    if  not singular :
        x = math.degrees(math.atan2(R[2][1] , R[2][2]))
        y = math.degrees(math.atan2(-R[2][0], sy))
        z = math.degrees(math.atan2(R[1][0], R[0][0]))
    else :
        x = math.degrees(math.atan2(-R[1][2], R[1][1]))
        y = math.degrees(math.atan2(-R[2][0], sy))
        z = 0

    logging.debug("Hand rotationMatrixToEulerAngles("+str(R)+") end")
    return Vec3f(x, y, z)

# class for sending http request
class VREDPyRequest(vrAEBase):
    _conn = None
    def __init__(self, host, port, simKey, timeValue = 1, fpsValue = 30):
        try:
            vrAEBase.__init__(self)
            initFindCache()
            self._conn = h.HTTPConnection(host, port, timeout=10)
            self.simKey = simKey
            self.fpsValue = fpsValue
            self.timeValue = timeValue
            self.SceneNodes = []
            self.counter = 0
            self.time2Sleep = (1/self.fpsValue)-0.00487
            self.startTransform = false
            self._conn.connect()
            self.getRequest()
            self.addLoop()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print("Internal error #11")
    
    def loop(self):
        if self.startTransform:
            if len(self.SceneNodes) > self.counter:
                mytime = datetime.datetime.time(datetime.datetime.now())
                print("SceneNode No. {} time {}".format(self.counter, mytime))
                for part in self.SceneNodes[self.counter].getPartOfNodes():
                    nodeName = part.getSubjects()[0]
                    if nodeName:
                       thisNode = findNode("KOLBEN")
                       #thisNode = findNode(nodeName)
                       if thisNode.isValid():
                            myX = part.getTransformationGroupNode().getTranslation3D().getVector3D().getX()
                            myY = part.getTransformationGroupNode().getTranslation3D().getVector3D().getY()
                            myZ = part.getTransformationGroupNode().getTranslation3D().getVector3D().getZ()
                            thisNode.setTranslation(np.float32(myX), np.float32(myY), np.float32(myZ))
                sleepingTime(self.time2Sleep)
                self.counter += 1             

    def getRequest(self):
        try:
            vrLogInfo(u.urlencode({self.simKey: '0', 'fps': self.fpsValue, 'time': self.timeValue}))
            userAndPass = b64encode("TEST:TEST").decode("ascii")
            headers = { 'Authorization' : 'Basic %s' %  userAndPass }
            self._conn.request("GET", "/?%s" % u.urlencode({self.simKey: '0', 'fps': self.fpsValue, 'time': self.timeValue}), headers=headers)
            response = self._conn.getresponse()
            if (response.status == 200):
                #return json.loads(json_data)
                sr = codecs.getreader("utf_8")(response)
                outStr = ""
                counter = 0
                for line in sr.readlines():
                    line = line.rstrip()
                    if ('</rdf:RDF>' not in line):
                        outStr += line
                    elif ('</rdf:RDF>'in line):
                        outStr +='</rdf:RDF>'
                        #print('counter: {}'.format(counter))
                        g = VisualisationStructure("",outStr)
                        newSceneNode = g.getSceneNodeData()
                        if newSceneNode:
                            self.SceneNodes.append(newSceneNode)
                            outStr = ''
                            counter += 1
                self.startTransform = true
            else:
                vrLogInfo(response.status)
                vrLogInfo(len(response.read()))
                vrLogInfo(response.read())
                vrLogInfo(response.read())
                return None
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print("Internal error #12")
    
    def terminate(self):
        # Beendet den Thread
        self.running = 0

class SceneNode:
    def __init__(self):
        self.Type = URIRef(SCENEGRAPH['SceneNode'])
        self.OSLCProperty = URIRef(SCENEGRAPH['sceneNode'])
        self.About = None
        self.PartOfNode = []
        self.Created = None
        self.Subjects = []

    def setAbout(self, About):
         self.About = URIRef(About)

    def setPartOfNodes(self, PartOfNode):
         self.PartOfNode = PartOfNode

    def addPartOfNode(self, PartOfNode):
         self.PartOfNode.append(PartOfNode)

    def setSubjects(self, thisSubjects):
        self.Subjects = thisSubjects

    def addSubject(self, Subject):
         self.Subjects.append(Subject)

    def setCreated(self, thisCreated):
        self.Created = thisCreated

    def getAbout(self):
         return URIRef(self.About)

    def getPartOfNodes(self):
        return self.PartOfNode

    def getSubjects(self):
        return self.Subjects

    def getCreated(self):
        return self.Created

    def getType(self):
        return self.Type

class PartOfNode:
    def __init__(self):
        self.Type = URIRef(SCENEGRAPH['PartOfNode'])
        self.OSLCProperty = URIRef(SCENEGRAPH['partOfNode'])
        self.About = None
        self.TransformationGroupNode = None
        self.Created = None
        self.Subjects = []

    def setAbout(self, About):
         self.About = URIRef(About)

    def setTransformationGroupNode(self, TransformationGroupNode):
         self.TransformationGroupNode = TransformationGroupNode

    def setSubjects(self, thisSubjects):
        self.Subjects = thisSubjects

    def addSubject(self, Subject):
         self.Subjects.append(Subject)

    def setCreated(self, thisCreated):
        self.Created = thisCreated

    def getAbout(self):
         return URIRef(self.About)

    def getTransformationGroupNode(self):
        return self.TransformationGroupNode

    def getSubjects(self):
        return self.Subjects

    def getCreated(self):
        return self.Created

    def getType(self):
        return self.Type

    def getOSLCProperty(self):
        return self.OSLCProperty

class TransformationGroupNode:
    def __init__(self):
        self.Type = URIRef(SCENEGRAPH['TransformationGroupNode'])
        self.OSLCProperty = URIRef(SCENEGRAPH['transformationGroupNode'])
        self.About = None
        self.Translation3D = None
        self.Rotation3D = None
        self.Created = None
        self.Subjects = []
        self.Title = None

    def setAbout(self, About):
         self.About = URIRef(About)

    def setTranslation3D(self, Translation3D):
         self.Translation3D = Translation3D

    def setRotation3D(self, Rotation3D):
         self.Rotation3D = Rotation3D

    def setSubjects(self, thisSubjects):
        self.Subjects = thisSubjects

    def addSubject(self, Subject):
         self.Subjects.append(Subject)

    def setCreated(self, thisCreated):
        self.Created = thisCreated

    def getAbout(self):
         return URIRef(self.About)

    def getTranslation3D(self):
        return self.Translation3D

    def getRotation3D(self):
        return self.Rotation3D

    def getSubjects(self):
        return self.Subjects

    def getCreated(self):
        return self.Created

    def getType(self):
        return self.Type
 
    def getOSLCProperty(self):
        return self.OSLCProperty

class Translation3D:
    def __init__(self):
        self.Type = URIRef(SPATIAL['translation3D'])
        self.OSLCProperty = URIRef(SPATIAL['translation3D'])
        self.About = None
        self.Vector3D = None
        self.Created = None
        self.Subjects = []
        self.Title = None

    def setAbout(self, About):
         self.About = URIRef(About)

    def setVector3D(self, Vector3D):
         self.Vector3D = Vector3D

    def getAbout(self):
         return URIRef(self.About)

    def getVector3D(self):
        return self.Vector3D

    def getCreated(self):
        return self.Created

    def getType(self):
        return self.Type
 
    def getOSLCProperty(self):
        return self.OSLCProperty

class Rotation3D:
    def __init__(self):
        self.Type = URIRef(SPATIAL['Rotation3D'])
        self.OSLCProperty = URIRef(SPATIAL['rotation3D'])
        self.About = None
        self.Matrix3D = None
        self.Created = None
        self.Subjects = []
        self.Title = None

    def setAbout(self, About):
         self.About = URIRef(About)

    def setMatrix3D(self, Matrix3D):
        return self.Matrix3D

    def getAbout(self):
         return URIRef(self.About)

    def getMatrix3D(self):
        return self.Matrix3D

    def getCreated(self):
        return self.Created

    def getSubjects(self):
        return self.Subjects

    def getTitle(self):
        return self.Title
    
    def getType(self):
        return self.Type
 
    def getOSLCProperty(self):
        return self.OSLCProperty

class Matrix3D:
    def __init__(self):
        self.Type = URIRef(MATHS['Matrix3D'])
        self.OSLCProperty = URIRef(MATHS['matrix3D'])
        self.About = None
        self.Created = None
        self.Subjects = []
        self.Title = None
        self.A11 = None
        self.A12 = None
        self.A13 = None
        self.A21 = None
        self.A22 = None
        self.A23 = None
        self.A31 = None
        self.A32 = None
        self.A33 = None
        self.Matrix = []

    def setAbout(self, About):
         self.About = URIRef(About)

    def setA11(self, A11):
        self.A11 = A11
    
    def setA12(self, A12):
        self.A12 = A12
    
    def setA13(self, A13):
        self.A13 = A13
    
    def setA21(self, A21):
        self.A21 = A21
    
    def setA22(self, A22):
        self.A22 = A22
    
    def setA23(self, A23):
        self.A23 = A23
    
    def setA31(self, A31):
        self.A31 = A31
    
    def setA32(self, A32):
        self.A32 = A32
    
    def setA33(self, A33):
        self.A33 = A33

    def getAbout(self):
         return URIRef(self.About)

    def getA11(self):
        return self.A11
    
    def getA12(self):
        return self.A12
    
    def getA13(self):
        return self.A13
    
    def getA21(self):
        return self.A21
    
    def getA22(self):
        return self.A22
    
    def getA23(self):
        return self.A23
    
    def getA31(self):
        return self.A31
    
    def getA32(self):
        return self.A32
    
    def getA33(self):
        return self.A33

    def getMatrix(self):
        return self.Matrix 
    
    def getType(self):
        return self.Type
 
    def getOSLCProperty(self):
        return self.OSLCProperty

class Vector3D:
    def __init__(self):
        self.Type = URIRef(MATHS['Vector3D'])
        self.OSLCProperty = URIRef(MATHS['vector3D'])
        self.About = None
        self.Created = None
        self.Subjects = []
        self.Title = None
        self.X = None
        self.Y = None
        self.Z = None
        self.XYZ = []

    def setAbout(self, About):
         self.About = URIRef(About)

    def setX(self, x):
        self.X = x

    def setY(self, y):
        self.Y = y

    def setZ(self, z):
        self.Z = z

    def setXYZ(self, XYZ):
        self.XYZ = XYZ

    def getAbout(self):
         return URIRef(self.About)

    def getX(self):
        return self.X

    def getY(self):
        return self.Y

    def getZ(self):
        return self.Z

    def getXYZ(self):
        return self.XYZ
    
    def getType(self):
        return self.Type
 
    def getOSLCProperty(self):
        return self.OSLCProperty

class VisualisationStructure:
    def __init__(self, oslcPath, oslcData):
        self.sceneNode = None
        try:
            self.graph = rdflib.Graph()
            if oslcPath:
                if os.path.exists(oslcPath):
                    self.graph.load(oslcPath)
                    print('Graph has been loaded')
            elif oslcData:
                #print(oslcData)
                self.graph.parse(format="xml", data=oslcData)
            else:
                print('error #OSLC parsing')
                return
                
            self.graph.bind('dc', DC)
            self.graph.bind('oslc', OSLC)
            self.graph.bind('oslc_data', OSLC_DATA)
            self.graph.bind('spatial', SPATIAL)
            self.graph.bind('scene', SCENE)
            self.graph.bind('sg', SCENEGRAPH)
            self.graph.bind('math', MATHS)
            self.graph.bind('syslm', SYSLM)
            self.graph.bind('xs', XSD)
            self.graph.bind('dcterms', DCTERMS)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print("Internal error #2")

    def getSubject(self, objURI):
        if (objURI, DCTERMS['subject'], None) in self.graph:
            for s,p,o in self.graph.triples((objURI, DCTERMS['subject'], None)):
                #print("Name: {}".format(o))
                return o
        else:
            return None

    def getCreated(self, objURI):
        if (objURI, DCTERMS['created'], None) in self.graph:
            for s,p,o in self.graph.triples((objURI, DCTERMS['created'], None)):
                #print("Created: {}".format(o))
                return o
        else:
            return None
    
    def getSceneNodeData(self):
        self.sceneNode = SceneNode()
        if (None, None, self.sceneNode.getType()) in self.graph:
            for s,p,o in self.graph.triples((None,  None, self.sceneNode.getType())):
                self.sceneNode.setAbout(s)
        else:
            return false

        subject = self.getSubject(self.sceneNode.getAbout())
        if subject:
            self.sceneNode.addSubject(subject)
        else:
            return false

        created = self.getCreated(self.sceneNode.getAbout())
        if created:
            self.sceneNode.setCreated(created)
        else:
            return false

        if (self.sceneNode.getAbout(), SCENEGRAPH['partOfNode'], None) in self.graph:
            for s,p,o in self.graph.triples((self.sceneNode.getAbout(), SCENEGRAPH['partOfNode'], None)):
                #print("URI: {}".format(o))
                partOfNode = PartOfNode()
                partOfNode.setAbout(o)
                partOfNode = self.getPartofNodeData(partOfNode)
                if partOfNode:
                    self.sceneNode.addPartOfNode(partOfNode)
        else:
            return false

        return self.sceneNode

    def getPartofNodeData(self, partOfNode):
        subject = self.getSubject(partOfNode.getAbout())
        if subject:
            partOfNode.addSubject(subject)
        else:
            return false
        
        created = self.getCreated(partOfNode.getAbout())
        if created:
            partOfNode.setCreated(created)
        else:
            return false
        
        transformationGroupNode = TransformationGroupNode()
        if (partOfNode.getAbout(), TransformationGroupNode().getOSLCProperty(), None) in self.graph:
            for s,p,o in self.graph.triples((partOfNode.getAbout(), TransformationGroupNode().getOSLCProperty(), None)):
                #print("URI: {}".format(o))
                transformationGroupNode.setAbout(o)
                transformationGroupNode = self.getTransformationGroupNodeData(transformationGroupNode)
                if transformationGroupNode:
                    partOfNode.setTransformationGroupNode(transformationGroupNode)
        else:
            return false
        
        return partOfNode

    def getTransformationGroupNodeData(self, transformationGroupNode):    
        created = self.getCreated(transformationGroupNode.getAbout())
        if created:
            transformationGroupNode.setCreated(created)
        else:
            return false

        translation3D = Translation3D()
        if (transformationGroupNode.getAbout(), translation3D.getOSLCProperty(), None) in self.graph:
            for s,p,o in self.graph.triples((transformationGroupNode.getAbout(), translation3D.getOSLCProperty(), None)):
                #print("URI: {}".format(o))
                translation3D.setAbout(o)
                translation3D = self.getTranslation3DData(translation3D)
                if translation3D:
                    transformationGroupNode.setTranslation3D(translation3D)
        else:
            return false

        rotation3D = Rotation3D()
        if (transformationGroupNode.getAbout(), rotation3D.getOSLCProperty(), None) in self.graph:
            for s,p,o in self.graph.triples((transformationGroupNode.getAbout(), rotation3D.getOSLCProperty(), None)):
                #print("URI: {}".format(o))
                rotation3D.setAbout(o)
                rotation3D = self.getRotation3DData(rotation3D)
                if rotation3D:
                    transformationGroupNode.setRotation3D(rotation3D)
        else:
            return false
        
        return transformationGroupNode

    def getTranslation3DData(self, translation3D):
        subject = self.getSubject(translation3D.getAbout())
        if subject:
            translation3D.addSubject(subject)
        
        created = self.getCreated(translation3D.getAbout())
        if created:
            translation3D.setCreated(created)
        
        vector3D = Vector3D()
        if (translation3D.getAbout(), vector3D.getOSLCProperty(), None) in self.graph:
            for s,p,o in self.graph.triples((translation3D.getAbout(), vector3D.getOSLCProperty(), None)):
                #print("URI: {}".format(o))
                vector3D.setAbout(o)
                vector3D = self.getVector3DData(vector3D)
                if vector3D:
                    translation3D.setVector3D(vector3D)
        else:
            return false

        return translation3D

    def getRotation3DData(self, Rotation3D):
        subject = self.getSubject(Rotation3D.getAbout())
        if subject:
            Rotation3D.addSubject(subject)
        
        created = self.getCreated(Rotation3D.getAbout())
        if created:
            Rotation3D.setCreated(created)

        matrix3D = Matrix3D()
        if (Rotation3D.getAbout(), matrix3D.getOSLCProperty(), None) in self.graph:
            for s,p,o in self.graph.triples((Rotation3D.getAbout(), matrix3D.getOSLCProperty(), None)):
                #print("URI: {}".format(o))
                matrix3D.setAbout(o)
                matrix3D = self.getMatrix3DData(matrix3D)
                if matrix3D:
                    Rotation3D.setMatrix3D(matrix3D)
        else:
            return false

        return Rotation3D

    def getVector3DData(self, vector3D):
        subject = self.getSubject(vector3D.getAbout())
        if subject:
            vector3D.addSubject(subject)
        
        created = self.getCreated(vector3D.getAbout())
        if created:
            vector3D.setCreated(created)

        x = self.getMathValues(vector3D.getAbout(), 'x')
        y = self.getMathValues(vector3D.getAbout(), 'y')
        z = self.getMathValues(vector3D.getAbout(), 'z')

        vector3D.setX(x)
        vector3D.setY(y)
        vector3D.setZ(z)

        return vector3D

    def getMatrix3DData(self, matrix3D):
        subject = self.getSubject(matrix3D.getAbout())
        if subject:
            matrix3D.addSubject(subject)
        
        created = self.getCreated(matrix3D.getAbout())
        if created:
            matrix3D.setCreated(created)

        a11 = self.getMathValues(matrix3D.getAbout(), 'a11')
        a12 = self.getMathValues(matrix3D.getAbout(), 'a12')
        a13 = self.getMathValues(matrix3D.getAbout(), 'a13')
        a21 = self.getMathValues(matrix3D.getAbout(), 'a21')
        a22 = self.getMathValues(matrix3D.getAbout(), 'a22')
        a23 = self.getMathValues(matrix3D.getAbout(), 'a23')
        a31 = self.getMathValues(matrix3D.getAbout(), 'a31')
        a32 = self.getMathValues(matrix3D.getAbout(), 'a32')
        a33 = self.getMathValues(matrix3D.getAbout(), 'a33')

        matrix3D.setA11(a11)
        matrix3D.setA12(a12)
        matrix3D.setA13(a13)
        matrix3D.setA11(a21)
        matrix3D.setA12(a22)
        matrix3D.setA13(a23)
        matrix3D.setA11(a31)
        matrix3D.setA12(a32)
        matrix3D.setA13(a33)

        return matrix3D

    def getMathValues(self, obj3D_URI, value):
            if (obj3D_URI, MATHS[value], None) in self.graph:
                for sValue, pValue, oValue in self.graph.triples((obj3D_URI,  MATHS[value], None)):
                    if (oValue, XSD['double'], None) in self.graph:
                        for s, p, double in self.graph.triples((oValue,  XSD['double'], None)):
                            #print("{} value: {}".format(value, double))
                            return double
        
def main(argv=None):
    try:
      print("Top")
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print("Internal error #1")

if __name__ == '__main__':
    #main()
    print("Top")

myRequest = VREDPyRequest("localhost", 9013, "nx_motion", 30, 30)    
myRequest.setActive(true)
