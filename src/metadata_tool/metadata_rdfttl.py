# coding=utf8
import sys
import os
import json
from rdflib import URIRef, BNode, Literal
from rdflib import Graph
from rdflib.namespace import RDF, DCTERMS, FOAF, XSD, NamespaceManager
from rdflib import Namespace


def jsonToTtl(read_file):
    metadatajson = json.load(read_file)

    # define URI of the data set
    datasetURI = URIRef("https://www.bsp.de/datasetBsp")

    # define namespaces in addition to the imported
    DCAT = Namespace("http://www.w3.org/ns/dcat#")
    OEO = Namespace("http://openenergy-platform.org/ontology/v0.0.1/oeo/")
    DCATDE = Namespace("http://dcat-ap.de/def/dcatde/")
    SCHEMA = Namespace("http://schema.org/")

    # initialize empty RDF-Graph
    g = Graph()

    # set prefixes for the namespaces
    g.namespace_manager.bind('foaf', FOAF)
    g.namespace_manager.bind('dct', DCTERMS)
    g.namespace_manager.bind('dcat', DCAT)
    g.namespace_manager.bind('dcatde', DCATDE)
    g.namespace_manager.bind('oeo', OEO)
    g.namespace_manager.bind('schema', SCHEMA)

    # DCAT Catalog
    catalogURI = URIRef("https://www.bsp.de/catalogBsp")
    g.add( (catalogURI, RDF.type, DCAT.Catalog))
    g.add( (catalogURI, DCTERMS.title, Literal("")))

    try:
        # DCAT Dataset
        g.add( (datasetURI, RDF.type, DCAT.Dataset))
        g.add( ( datasetURI, DCTERMS.title, Literal(metadatajson["title"]) ) )
        # --- description language tag ?
        g.add( ( datasetURI, DCTERMS.description, Literal(metadatajson["description"]) ) )
        # language ---
        print str(type(metadatajson["language"]))
        langdict = {
            'eng' : 'http://publications.europa.eu/resource/authority/language/ENG',
            'en-GB' : 'http://publications.europa.eu/resource/authority/language/ENG',
            'ger' : 'http://publications.europa.eu/resource/authority/language/GER'
        }
        for lang in metadatajson["language"][:]:
            g.add( ( datasetURI, DCTERMS.language, URIRef(langdict[lang]) ) )

        # keywords
        if "keywords" in metadatajson: #---
            for k in metadatajson["keywords"]:
                g.add( ( datasetURI, DCAT.keyword, Literal(k) ) )

        # sources
        for source in metadatajson["sources"][:]:
            s = BNode()
            # ---
            g.add( ( datasetURI, DCTERMS.source, s ) )
            try:
                g.add( ( s, DCTERMS.title, Literal(source["name"]) ) )
            except:
                print("source without name")
            g.add( ( s, DCTERMS.description, Literal(source["description"]) ) )
            # --- url
            g.add( ( s, DCTERMS.accessRights, Literal(source["license"]) ) )
            # ----
            g.add( ( s, DCTERMS.RightsStatement, Literal(source["copyright"]) ) )

        # license
        # ---
        licdict = {
            'ODbL-1.0' : 'https://www.dcat-ap.de/def/licenses/odbl'
        }
        try:
            g.add( ( datasetURI, DCTERMS.license, URIRef(licdict[metadatajson["license"]["id"]])))
        except:
            # ---
            g.add( ( datasetURI, DCTERMS.license, Literal(metadatajson["license"]["id"])))
        # ---
        g.add( ( datasetURI, DCATDE.licenseAttributionByText, Literal(metadatajson["license"]["instruction"])))

        # cotributors ---
        for contributor in metadatajson["contributors"]:
            c = BNode()
            g.add( ( datasetURI, DCTERMS.contributor, c))
            g.add( ( c, RDF.type, FOAF.Person))
            g.add( ( c, FOAF.name, Literal(contributor["name"])))
            g.add( ( c, FOAF.mbox, Literal(contributor["email"])))
            g.add( ( c, OEO.date, Literal(contributor["date"]))) # xsd:date ?
            g.add( ( c, OEO.comment, Literal(contributor["comment"]))) #rdfs:comment ?

        # temporal
        if "temporal" in metadatajson:
            t = BNode()
            g.add( (datasetURI, DCTERMS.temporal, t))
            g.add( (t, RDF.type, DCTERMS.PeriodOfTime) )
            g.add( (t, SCHEMA.startDate, Literal(metadatajson["temporal"]["start"])))
            g.add( (t, SCHEMA.endDate, Literal(metadatajson["temporal"]["end"])))
            g.add( (t, OEO.t_resolution, Literal(metadatajson["temporal"]["resolution"])))

    except Exception, e:
        print "problem with: " + str(e)

    filename, file_extension = os.path.splitext(read_file.name)
    i = 0
    while True:
        d = filename + '_'+ str(i) + '.ttl'
        if not os.path.exists(d):
            g.serialize(destination=d, format='turtle')
            print d
            break
        i += 1
    return

def ttlToJson(read_file):
    reload(sys)
    sys.setdefaultencoding('utf8')
    g = Graph()
    print("name: " + read_file.name)
    g.parse(read_file, format="ttl")
    #print g.serialize(format='turtle')
    # for s, o in subject_objects(DCTERMS.title):
    #     print(str(o))
    jsondict = {}
    strh = ""
    for s,p,o in g.triples( (None,  DCTERMS.title, None) ):
        strh = strh + str(o) + "\n"
    jsondict['title'] = strh
    print jsondict
    # for t in g.triples():
    #     print str(t)
    strh = ""
    for s,p,o in g.triples( (None,  DCTERMS.description, None) ):
        strh = strh + str(o) + "\n"
    jsondict['description'] = strh
    print jsondict

    jsondict['abc'] = "123"

    lang = []
    for s,p,o in g.triples( (None,  DCTERMS.language, None) ):
        lang.append(o.rsplit('/', 1)[1].lower())
    lang = list(set(lang))
    print lang
    jsondict['language'] = lang
    print jsondict

    ##### sources #####
    sources = []
    for s,p,o in g.triples( (None,  DCTERMS.source, None) ):
        source = {}
        source['title'] = str(g.objects((o,DCTERMS.title)))
        # for s2,p2,o2 in g.triples( (o,  DCTERMS.title, None) ):
        sources.append(source)
    jsondict['sources'] = sources

    filename, file_extension = os.path.splitext(read_file.name)

    i = 0
    while True:
        d = filename + '_'+ str(i) + '.json'
        if not os.path.exists(d):
            with open(filename+"_"+str(i)+".json", "w") as write_file:
                json.dump(jsondict, write_file, indent=4)
                print d
            break
        i += 1

    return

if __name__ == '__main__':
    print sys.argv[:]
    if(len(sys.argv) != 2):
        print("usage: ")
        exit()
    path = sys.argv[1]
    try:
        filename, file_extension = os.path.splitext(path)
        print filename + "\t" + file_extension
        with open(path, "r") as read_file:
            print("name: " + read_file.name)
            if(file_extension == '.json'):
                print "1"
                jsonToTtl(read_file)
            elif(file_extension == '.ttl'):
                print "2"
                ttlToJson(read_file)
            else:
                print("json or ttl file please")
    except Exception, e:
        print(e)
    #main(sys.argv[1:])
    print("Ende")
