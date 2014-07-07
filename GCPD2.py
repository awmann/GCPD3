#!/usr/bin/env python
""" A module to check GCPD database
See http://www.python9.org/p9-zadka.ppt for
tutorial

Generally, using http://wwwsearch.sourceforge.net/ClientForm/ wis a good idea
but if we want to distribute it we  want to minimize external dependencies
we may want to do something simpler....
""" 
import types
import string

class GCPD_No_Data(ValueError): pass
class StarNameException(ValueError): pass
class ParseError(Exception): pass

def to_float(str):
    """ Helper function for parsing data with some data omitted
    Example:
    >>> to_float('3.14') # doctest:+ELLIPSIS
    3.14...
    >>> to_float('  ')
    ''

    """ 
    try:
        return float(str)
    except ValueError:
        return ''

def safe_add(fl,st):
    """Helper function for parsing data with some data omitted.
    If second value is not parsable, return empty string.

    >>> safe_add(1,'4')
    5.0
    >>> safe_add(1,'a')
    ''
    >>> safe_add(1,'')
    ''
    """
    try:
        return float(fl)+float(st)
    except ValueError:
        return ''
    except TypeError:
        return ''
    
def safe_sub(fl,st):
    """Helper function for parsing data with some data omitted.
    If second value is not parsable, return empty string.

    >>> safe_sub(1,'4')
    -3.0
    >>> safe_sub(1,'a')
    ''
    >>> safe_sub(1,'')
    ''

    """
    try:
        return float(fl)-float(st)
    except ValueError:
        return ''
    except TypeError:
        return ''

def add_list(l1,l2):
    """Helper function for parsing data with some data omitted.
    >>> add_list([1,'4.56', '*'], ['-1', '100', '1000']) #doctest: +NORMALIZE_WHITESPACE
    [0.0, 104.56, '']

    """
    r=[]
    for x1,x2 in zip(l1,l2):
        try:
            r.append(float(x1)+float(x2))
        
        except ValueError:
            r.append( '')
        except TypeError:
            r.append('')
    return r

def sub_list(l1,l2):
    """Helper function for parsing data with some data omitted.
    >>> sub_list([1,'4.75', '*'], ['-1', 1, '1000']) #doctest: +NORMALIZE_WHITESPACE
    [2.0, 3.75, '']


    """
    r=[]
    for x1,x2 in zip(l1,l2):
        try:
            r.append(float(x1)-float(x2))
        
        except ValueError:
            r.append( '')
        except TypeError:
            r.append('')
    return r


def translate_name(starname):
    """ Here is translation definition:
    from http://obswww.unige.ch/gcpd/basicdef.html#large

    HD and HDE, SAO, HIC, PPM Catalogues

    100BBBBBB : HD and HDE
    150BBBBBB : SAO
    160BBBBBB : Hipparcos HIC
    170BBBBBB : PPM

    Example:
    >>> translate_name('HD174881')
    '0100174881'
    >>> translate_name('HIP1')
    '0160000001'

    """
    rg=re.match("(?P<catalog>\D*)(?P<number>\d+)",starname)
    if rg:
        catalog=rg.group('catalog')
        number=int(rg.group('number'))
        if catalog in ['HD', 'HDE', 'HDC']:
            return "0100%06d" %number
        elif catalog=='SAO':
            return "0150%06d" %number
        elif catalog in ['HIP', 'HIC']:
            return "0160%06d" %number
        elif catalog=='PPM':
            return "0170%06d" %number
        else:
            #raise StarNameException(starname)
            return starname
    else:
        return starname # may be it is ok?
        

import urllib, sys,htmllib,formatter,re
import getopt

class GCPD_table_parser(htmllib.HTMLParser):
    """ Parse a table describing which systems are available
    for given star
    """
    def __init__(self,*args, **kw):
        htmllib.HTMLParser.__init__(self,*args, **kw)
        self.row=0
        self.column=0
        self.syslist=[]
        self.sys_number_list=[]
        self.inside_tr=False
        self.inside_b=False
        self.inside_table=False
        self.inside_th=False
        self.inside_td=False
        self.description=[]
        self.inside_b=False
        self.inside_a=False

    def start_th(self,attr):
        self.inside_th=True
        
    def end_th(self):
        if not self.inside_th:
            raise ParseError, "end of th without start"
        self.inside_th=False
        
    
    def start_table(self,attr):
        self.inside_table=True

    def end_table(self):
        self.inside_table=False

        
    def start_tr(self,attr):
        self.inside_tr=True
        
    def end_tr(self):
        self.column=0
        self.row+=1
        self.inside_tr=False

    def start_td(self,attr):
        self.inside_td=True
    def end_td(self): 
        self.inside_td=False
        self.column+=1

    def start_b(self,attr):
        self.inside_b=True
    def end_b(self): 
        self.inside_b=False

    def start_a(self,attr):
        self.inside_a=True
    def end_a(self): 
        self.inside_a=False



    def inside_description(self):
        return (self.inside_table and self.inside_tr and (self.row==0))

    def handle_data(self,data):
        if self.inside_th and self.inside_description():
            self.description.append(data.strip() )
        elif self.inside_td and  self.inside_a and \
                 self.description[self.column]=='Designation':
            self.syslist.append(data.strip())
        elif self.inside_td  and self.inside_a and\
                 self.description[self.column]=='System':
            self.sys_number_list.append(data.strip())
            
def GCPD_system_list(starname,rem):
    action_url='http://obswww.unige.ch/gcpd/cgi-bin/genIndex.cgi'
    params = urllib.urlencode({'ident':translate_name(starname),
                               'button':'Query by Star Number'})
    f = urllib.urlopen(action_url, params)
   

    h = GCPD_table_parser(formatter.NullFormatter())
    s=f.read()
    h.feed(s)
    f.close()
    if len(h.syslist)==0:
        raise GCPD_No_Data
    return h.syslist
    
    
class GCPD_parser(htmllib.HTMLParser):
    """ 
    """
    metadata={'Star Name:':'starname',
              'Star Code:':'starcode',
              'Rem:':'rem',
              'Nb Sources:':'number_of_sources',
              'References:':'references_num'}
    error_message='No values'.upper()
    def __init__(self, *args, **kw):
        htmllib.HTMLParser.__init__(self,*args, **kw)
        self.inside_b=False
        self.waiting_for_data_b=False
        self.hr_number=0
        self.references=[]
        self.metadata_section=0
        self.inside_h3=False
        #self.starting_ref=False

    def inside_ref_section(self):
        return self.hr_number==self.metadata_section+2

    def inside_data_section(self):
        return self.hr_number==self.metadata_section+1

    def start_pre(self,data):
        if self.inside_ref_section():
            self.current_reference={}


    def end_pre(self):
        """ Photometry data -- the last before /pre
        This simple algorithm chokes on 13-color photometry system
        """
        if self.inside_data_section():
            self.photo_data=self.last_postb_data
            self.column_names=self.b_name.split('\t')
        if self.inside_ref_section():
            self.references.append(self.current_reference)
            
        
    def handle_data(self,data):
       
        cd=data.upper()
        dd=data.strip()
        if re.match(self.error_message,cd):
            raise GCPD_No_Data
        if self.inside_b:
            self.b_name=data #Not dd!
        if self.inside_h3:
            if data.upper().strip()=='Selection:'.upper():
                self.metadata_section=self.hr_number
        
        if self.waiting_for_data_b and not self.inside_b:
            for k in self.metadata:
                if re.match(k,self.b_name):
                    setattr(self,self.metadata[k],dd)
            if self.inside_data_section():
                self.waiting_for_data_b=False
                self.last_postb_data=data
            elif self.inside_ref_section():
                if dd!='':
                    self.current_reference[self.b_name]=dd
                    self.waiting_for_data_b=False

    def start_h3(self,attrs):
        self.inside_h3=True
    def end_h3(self):
        self.inside_h3=False
        
    def start_b(self,attrs):
        self.inside_b=True
        self.waiting_for_data_b=True

    def end_b(self):
        self.inside_b=False

    def start_a(self,attr):
        if self.waiting_for_data_b and self.b_name.upper()=='BIBCODE':
            if attr[0][0] == "href" :
                url=attr[0][1]
                if url[-1]!='?': # query with no parameters
                    self.current_reference['BibcodeURL']=url
          

    def start_hr(self,attrs):
        """ Horizontal rulers separate sections
        """
        self.hr_number+=1
        
   

class _GCPD:
    ""
    query_type    ='original'
    GCPD_action="http://obswww.unige.ch/gcpd/cgi-bin/photoSys.cgi?"
   
    
    def fetch_data(self,starname,rem):
        d={}
        d['phot']=self.system_string
        d['type']=self.query_type                # as mean or ...
        d['refer']='with'
        d['ident']=translate_name(starname)
        d['mode']='starno'
        query = urllib.urlencode(d)+'&rem='+rem
        op=urllib.URLopener().open
        f=op(self.GCPD_action+query)
        h = GCPD_parser(formatter.NullFormatter())
        s=f.read()
        h.feed(s)
        f.close()

        return h
        

    def parse_data(self,column_names,lines):
        
        nph=len(lines)
        splitlines=[l.split('\t') for l in lines]
        d={}
        for i in range(len(column_names)):
            n=column_names[i].strip()
            if len(n)>0:
                data=[]
                for j in range(nph):
                    if len(splitlines[j])>=i+1:
                        data.append(splitlines[j][i])
                    else:
                        data.append('')
                d[n]=data
                #this gets every i-th entry in all nonempty lines
        return d
        
    def print_data(self,target,rem,references=True):
        h=self.fetch_data(target,rem)
        photo_lines=[l  for l in h.photo_data.split('\n') if len(l.strip())>0]
        data= self.parse_data( h.column_names, photo_lines)
        d=self.process_data(data)
        r=[ "# data in %s photometric system" % self.system_string]
        for n in self.bands:
            for M in d[n]:
                if type(M)==types.FloatType:
                    r.append("M   %s %s %s %.4g 0.05 # %s %s" %(target, self.system_common_name, n, M, self.system_common_name, n))
        if references:
            r.append('# References:')
            r.append('#')
            for ref in h.references:

                for k in ['Author', 'Journal', 'Title', 'BibcodeURL']:
                    if k in ref:
                        field=re.sub(r'\n|\t', ' ', ref[k],0)
                        r.append('# ' + k +': ' + field)
                r.append('#')
            
        return '\n'.join(r)
        
class _GCPD2:
    ""
    query_type    ='original'
    GCPD_action="http://obswww.unige.ch/gcpd/cgi-bin/photoSys.cgi?"
   
    
    def fetch_data(self,starname,rem):
        d={}
        d['phot']=self.system_string
        d['type']=self.query_type                # as mean or ...
        d['refer']='with'
        d['ident']=translate_name(starname)
        d['mode']='starno'
        query = urllib.urlencode(d)+'&rem='+rem
        op=urllib.URLopener().open
        f=op(self.GCPD_action+query)
        h = GCPD_parser(formatter.NullFormatter())
        s=f.read()
        h.feed(s)
        f.close()

        return h
        

    def parse_data(self,column_names,lines):
        
        nph=len(lines)
        splitlines=[l.split() for l in lines]
        d={}
        for i in range(len(column_names)):
            n=column_names[i].strip()
            if len(n)>0:
                data=[]
                for j in range(nph):
                    if len(splitlines[j])>=i+1:
                        data.append(splitlines[j][i])
                    else:
                        data.append('')
                d[n]=data
                #this gets every i-th entry in all nonempty lines
        return d
        
    def print_data(self,target,rem,references=True):
        h=self.fetch_data(target,rem)
        
        photo_lines=[l  for l in h.photo_data.split('\n') if len(l.strip())>0]
	del h.column_names[0]
        data= self.parse_data( h.column_names, photo_lines)
        d=self.process_data(data)
        r=[ "# data in %s photometric system" % self.system_string]
        for n in self.bands:
            for M in d[n]:
                if type(M)==types.FloatType:
                    r.append("M   %s %s %s %.4g 0.05 # %s %s" %(target, self.system_common_name, n, M, self.system_common_name, n))

        if references:
            r.append('# References:')
            r.append('#')
            for ref in h.references:

                for k in ['Author', 'Journal', 'Title', 'BibcodeURL']:
                    if k in ref:
                        field=re.sub(r'\n|\t', ' ', ref[k],0)
                        r.append('# ' + k +': ' + field)
                r.append('#')
            
        return '\n'.join(r)
        
class GCPD_Photometry_UBV(_GCPD):
    """ UBV photometry.

    Example:
    >>> g=GCPD_Photometry_UBV()
    >>> g.bands
    ['U', 'B', 'V']
    >>> print g.print_data('HD184313') #doctest: +NORMALIZE_WHITESPACE
    # data in UBV photometric system
    M   HD184313 Johnson U 9.35 0.05 # Johnson U
    M   HD184313 Johnson U 9.63 0.05 # Johnson U
    M   HD184313 Johnson B 7.9 0.05 # Johnson B
    M   HD184313 Johnson B 8.13 0.05 # Johnson B
    M   HD184313 Johnson V 6.33 0.05 # Johnson V
    M   HD184313 Johnson V 6.45 0.05 # Johnson V
    # References:
    #
    # Author: Wisse P.N.J.
    # Journal: (1981) Astron. Astrophys. Suppl. 44, 273
    # Title: Three colour observations of southern red variable giant stars
    # BibcodeURL: http://adsabs.harvard.edu/cgi-bin/bib_query?1981A%26AS%2E%2E%2E44%2E%2E273W
    #
    # Author: Eggen O.J.
    # Journal: (1973) Mem. Roy. Astron. Soc. 77, 159
    # Title: Some small amplitude red variables of the disk and and halo  populations
    #
    """
    system_string='UBV'
    system_common_name='Johnson'
   
    bands=list(system_string) # this gives standard ordering of bands,
                              # useful for testing

    def process_data(self,d):
        
        V=[to_float(v) for v in d['V']]
        B=[safe_add(v,bv) for v,bv in zip(V,d['B-V'])]
        U=[safe_add(b,ub) for b,ub in zip(B,d['U-B'])]

        return {'U':U,'B':B,'V':V}

class GCPD_Photometry_UBVE(_GCPD):
    """ UBVE photometry.
    """
    system_string='UBVE'
    system_common_name='Johnson'
   
    bands=list('UBV') # this gives standard ordering of bands,
                              # useful for testing

    def process_data(self,d):
        
        V=[to_float(v) for v in d['V']]
        B=[safe_add(v,bv) for v,bv in zip(V,d['B-V'])]
        U=[safe_add(b,ub) for b,ub in zip(B,d['U-B'])]

        return {'U':U,'B':B,'V':V}

class GCPD_Photometry_UBVRI(_GCPD):
    """ UBVRI photometry.
    """
    system_string='UBVRI'
    system_common_name='Johnson'
   
    bands=list(system_string) # this gives standard ordering of bands,
                              # useful for testing

    def process_data(self,d):
        
        V=[to_float(v) for v in d['V']]
        B=[safe_add(v,bv) for v,bv in zip(V,d['B-V'])]
        U=[safe_add(b,ub) for b,ub in zip(B,d['U-B'])]
        R=[safe_sub(v,vr) for v,vr in zip(V,d['V-R'])]
        I=[safe_sub(r,ri) for r,ri in zip(R,d['R-I'])]

        return {'U':U,'B':B,'V':V,'R':R,'I':I}

class GCPD_Photometry_IJHKLMN(_GCPD):
    """ IJHKLMN photometry.
    """
    system_string='IJHKLMN'
    system_common_name='Johnson'
   
    bands=list('JHKLMN') # this gives standard ordering of bands,
                              # useful for testing

    def process_data(self,d):
        
        J=[to_float(j) for j in d['J']]
        H=[to_float(h) for h in d['H']]
        K=[to_float(k) for k in d['K']]
        L=[to_float(l) for l in d['L']]
        M=[to_float(m) for m in d['M']]
        N=[to_float(n) for n in d['N']]

        return {'J':J,'H':H,'K':K,'L':L,'M':M,'N':N}

class GCPD_Photometry_RI_Eggen(_GCPD):
    """ (RI)Eggen photometry.
    """
    system_string='(RI)Eggen'
    system_common_name='Eggen'
   
    bands=list('VRI') # this gives standard ordering of bands,
                              # useful for testing

    def process_data(self,d):
        
        V=[to_float(v) for v in d['V']]
        R=[safe_sub(v,vr) for v,vr in zip(V,d['V-R'])]
        for e in range(len(R)):
            if R[e] == '':
                R[e]=[to_float(r) for r in d['R']][e]
        I=[safe_sub(r,ri) for r,ri in zip(R,d['R-I'])]
        for e in range(len(I)):
            if I[e] == '':
                I[e]=[to_float(i) for i in d['I']][e]
                
        return {'V':V,'R':R,'I':I}

class GCPD_Photometry_RI_Cousins(_GCPD):
    """ (RI)Cousins photometry.
    """
    system_string='(RI)Cousins'
    system_common_name='Cousins'
   
    bands=list('UBVRI') # this gives standard ordering of bands,
                              # useful for testing
    def process_data(self,d):
        #print 'hi'
        V=[to_float(v) for v in d['V']]
        B=[safe_add(v,bv) for v,bv in zip(V,d['B-V'])]
        U=[safe_add(b,ub) for b,ub in zip(B,d['U-B'])]
        I=[safe_sub(v,vi) for v,vi in zip(V,d['V-I'])]
        R=[safe_add(i,ri) for i,ri in zip(I,d['R-I'])]
        #return {'V':V}
        return {'U':U,'B':B,'V':V,'R':R,'I':I}

class GCPD_Photometry_RI_Kron(_GCPD):
    """ (RI)Kron photometry.
    """
    system_string='(RI)Kron'
    system_common_name='Kron'
   
    bands=list('VRI') # this gives standard ordering of bands,
                              # useful for testing

    def process_data(self,d):
        
        V=[to_float(v) for v in d['V']]
        R=[safe_sub(v,vr) for v,vr in zip(V,d['V-R'])]
        for e in range(len(R)):
            if R[e] == '':
                R[e]=[to_float(r) for r in d['R']][e]
        I=[safe_sub(r,ri) for r,ri in zip(R,d['R-I'])]
        for e in range(len(I)):
            if I[e] == '':
                I[e]=[to_float(i) for i in d['I']][e]

        return {'V':V,'R':R,'I':I}

class GCPD_Photometry_Vilnius(_GCPD):
    """ Vilnius photometry.

    Example:
   >>> g=GCPD_Photometry_Vilnius()
   >>> g.bands
   ['U', 'P', 'X', 'Y', 'Z', 'V', 'S']
   >>> print g.print_data('HD432',references=False)  #doctest: +NORMALIZE_WHITESPACE
   # data in Vilnius photometric system
   M   HD432 Vilnius U 4.51 0.05 # Vilnius U
   M   HD432 Vilnius U 4.56 0.05 # Vilnius U
   M   HD432 Vilnius P 3.87 0.05 # Vilnius P
   M   HD432 Vilnius P 3.91 0.05 # Vilnius P
   M   HD432 Vilnius X 3.19 0.05 # Vilnius X
   M   HD432 Vilnius X 3.21 0.05 # Vilnius X
   M   HD432 Vilnius Y 2.64 0.05 # Vilnius Y
   M   HD432 Vilnius Y 2.65 0.05 # Vilnius Y
   M   HD432 Vilnius Z 2.43 0.05 # Vilnius Z
   M   HD432 Vilnius Z 2.43 0.05 # Vilnius Z
   M   HD432 Vilnius V 2.27 0.05 # Vilnius V
   M   HD432 Vilnius V 2.27 0.05 # Vilnius V
   M   HD432 Vilnius S 1.87 0.05 # Vilnius S
   M   HD432 Vilnius S 1.89 0.05 # Vilnius S
   """
    system_string='Vilnius'
    system_common_name='Vilnius'
   
    bands=list('UPXYZVS') # this gives standard ordering of bands,
                         # useful for testing

    def process_data(self,d):
        
        V=[to_float(v) for v in d['V']]
        S=[safe_sub(v,vs) for v,vs in zip(V,d['V-S'])]
        Z=[safe_add(v,zv) for v,zv in zip(V,d['Z-V'])]
        Y=[safe_add(z,yz) for z,yz in zip(Z,d['Y-Z'])]
        X=[safe_add(y,xy) for y,xy in zip(Y,d['X-Y'])]
        P=[safe_add(x,px) for x,px in zip(X,d['P-X'])]
        U=[safe_add(p,up) for p,up in zip(P,d['U-P'])]

        return dict([(k,locals()[k]) for k in self.bands])

class GCPD_Photometry_Straizys(GCPD_Photometry_Vilnius):
    """ Straizis photometry.

    """
    system_string='Straizys'
    system_common_name='Straizys'
   
    
class GCPD_Photometry_ubvy(_GCPD):
    """ ubvy photometry.
    
    Example:
    >>> g=GCPD_Photometry_ubvy() #doctest: +NORMALIZE_WHITESPACE
    >>> print g.print_data('HD172167',references=False)
    # data in uvby photometric system
    M   HD172167 Stromgren u 1.007 0.05 # Stromgren u
    M   HD172167 Stromgren u 0.928 0.05 # Stromgren u
    M   HD172167 Stromgren b -0.134 0.05 # Stromgren b
    M   HD172167 Stromgren b -0.161 0.05 # Stromgren b
    M   HD172167 Stromgren v 0.04 0.05 # Stromgren v
    M   HD172167 Stromgren v 0 0.05 # Stromgren v
    M   HD172167 Stromgren y -0.128 0.05 # Stromgren y
    M   HD172167 Stromgren y -0.165 0.05 # Stromgren y
    M   HD172167 Stromgren beta 2.907 0.05 # Stromgren beta
    M   HD172167 Stromgren beta 2.903 0.05 # Stromgren beta
   """
    system_string='uvby'
    system_common_name='Stromgren'
    bands=['u', 'b', 'v', 'y', 'beta']
    
    def process_data(self,d):
        #m1-(v-b)-(b-y)
        #c1=(u-v)-(v-b)
        y=[to_float(vv) for vv in d['V']]
        m1=[to_float(mm) for mm in d['m1']]
        c1=[to_float(cc) for cc in d['c1']]
        b_m_y=[to_float(mm) for mm in d['b-y']]

        b=[safe_add(vv,bmy) for vv,bmy in zip(y,b_m_y)]
 
        v2=[safe_add(bb2,mm2) for bb2,mm2 in zip(b,m1)]
        v1=[safe_sub(bb1,y1) for bb1,y1 in zip(b,y)]
        v=[safe_add(vv1,vv2) for vv1,vv2 in zip(v1,v2)]

        u2=[safe_add(cc1,vv3) for cc1,vv3 in zip(c1,v)]
        u1=[safe_sub(vv4,bb3) for vv4,bb3 in zip(v,b)]
        u=[safe_add(uu1,uu2) for uu1,uu2 in zip(u1,u2)]

        beta=[to_float(bb) for bb in d['beta']]
       
        return dict([(k,locals()[k]) for k in self.bands])

class GCPD_Photometry_Geneva(_GCPD):
    """ Geneva photometry.
    
    Example:
    #>>> g=GCPD_Photometry_Geneva()
    #>>> g.bands
    #['U', 'B', 'B1', 'B2', 'V1', 'G', 'V']
    #>>> print g.print_data('Sirius',references=False) #doctest: +NORMALIZE_WHITESPACE
    # data in Geneva photometric system
    M   Sirius -1.441 0.05 # Geneva VM
    M   Sirius 1.409 0.05 # Geneva U
    M   Sirius 0.949 0.05 # Geneva V
    M   Sirius 0.888 0.05 # Geneva B1
    M   Sirius 1.498 0.05 # Geneva B2
    M   Sirius 1.656 0.05 # Geneva V1
    M   Sirius 2.157 0.05 # Geneva G
 
    """
    system_string='Geneva'
    system_common_name='Geneva'
    bands=['V', 'B', 'U', 'B1', 'B2', 'V1', 'G']
    
  
    def process_data(self,d):
        """print d"""
        V=[to_float(v) for v in d['VM']]
        B=[safe_sub(v,bv) for v,bv in zip(V,d['V'])]
        U=[safe_add(bv,ub) for bv,ub in zip(B,d['U'])]
        B1=[safe_add(b1,bv) for b1,bv in zip(B,d['B1'])]
        B2=[safe_add(b2,bv) for b2,bv in zip(B,d['B2'])]
        V1=[safe_add(v1,bv) for v1,bv in zip(B,d['V1'])]
        G=[safe_add(g,bv) for g,bv in zip(B,d['G'])]

        return {'U':U,'B':B,'V':V,'B1':B1,'B2':B2,'V1':V1,'G':G}


    
class GCPD_Photometry_Walraven(_GCPD):
    """ Walraven photometry.
    
    Example:
    #>>> w=GCPD_Photometry_Walraven()
    #>>> w.bands
    ['V', 'B', 'L', 'U', 'W']
    #>>> print w.print_data('HD210934',references=False) #doctest: +NORMALIZE_WHITESPACE
    # data in Walraven photometric system
    M   HD210934 0.573 0.05 # Walraven V
    M   HD210934 0.613 0.05 # Walraven B
    M   HD210934 0.547 0.05 # Walraven L
    M   HD210934 0.382 0.05 # Walraven U
    M   HD210934 0.344 0.05 # Walraven W
    """
    
    system_string='Walraven'
    system_common_name='Walraven'
    bands=list('VBLUW')
    #bands=['V', 'B', 'L','U','W']
    def process_data(self,d):
        V=[to_float(s) for s in d['V']]
        B=[safe_add(v,vb) for v,vb in zip(V,d['V-B'])]
        U=[safe_sub(b,bu) for b,bu in zip(B,d['B-U'])]
        W=[safe_sub(u,uw) for u,uw in zip(U,d['U-W'])]
        L=[safe_sub(b,bl) for b,bl in zip(B,d['B-L'])]
        VJ=[to_float(s) for s in d['VJ']]
        return {'V':V,'B':B,'U':U,'W':W,'L':L,'VJ':VJ}
        """return dict([(k,locals()[k]) for k in self.bands])"""
    
class GCPD_Photometry_DDO(_GCPD):
    """ DDO photometry.
    
    
    Example:
    >>> dd=GCPD_Photometry_DDO()
    >>> dd.bands
    ['48', '51', '45', '42', '41', '38', '35']
    >>> print dd.print_data('-206700604',references=False) #doctest: +NORMALIZE_WHITESPACE
    # data in DDO photometric system
    M   -206700604 DDO 48 10.86 0.05 # DDO 48
    M   -206700604 DDO 45 12.13 0.05 # DDO 45
    M   -206700604 DDO 42 12.92 0.05 # DDO 42
    M   -206700604 DDO 41 13.01 0.05 # DDO 41
    """
    system_string='DDO'
    system_common_name='DDO'
    bands=['m48', 'm51', 'm45', 'm42', 'm41', 'm38', 'm35']

    def process_data(self,d):
        V48=[to_float(s) for s in d['V48']]
        V51=sub_list(V48, d['C4851'])
        V45=add_list(V48, d['C4548'])
        V42=add_list(V45, d['C4245'])
        V41=add_list(V42, d['C4142'])
        V38=add_list(V41, d['C3841'])
        V35=add_list(V38, d['C3538'])
        
        return dict([(b,locals()['V'+string.lstrip(b,'m')]) for b in self.bands])

class GCPD_Photometry_Oja(_GCPD):
    """ Oja photometry.
    """
    system_string='Oja'
    system_common_name='Oja'
    bands=['m45', 'm42', 'm41']

    def process_data(self,d):

        M45=[to_float(s) for s in d['m45']]
        M42=add_list(M45, d['ge'])
        M41=add_list(M42, d['ce'])
        
        return dict([(b,locals()['M'+string.lstrip(b,'m')]) for b in self.bands])

class GCPD_Photometry_13_color(_GCPD):
    """ 13-color photometry.
    """
    system_string='13-color'
    system_common_name='13-color'
    bands=['m52','m33','m35','m37','m40','m45','m63','m58','m72','m80','m86','m99','m110']
    
    def process_data(self,d):
        print d
        M52=[to_float(s) for s in d['52']]
        M33=add_list(M52, d['33-52'])
        M35=add_list(M52, d['35-52'])
        M37=add_list(M52, d['37-52'])
        M40=add_list(M52, d['40-52'])
        M45=add_list(M52, d['45-52'])
        M52=add_list(M52, d['52-52'])
        M63=add_list(M52, d['63-52'])
        M58=add_list(M52, d['58-52'])
        M72=sub_list(M58, d['72-58'])
        M80=sub_list(M58, d['80-58'])
        M86=sub_list(M58, d['86-58'])
        M99=sub_list(M58, d['99-58'])
        M110=sub_list(M58, d['110-58'])
        return dict([(b,locals()['M'+string.lstrip(b,'m')]) for b in self.bands])


class GCPD_Photometry_Alexander(_GCPD2):
    """ Alexander photometry from Jones, D. H. P., et al. 1981, MNRAS, 194, 403
    """

    system_string='Alexander'
    system_common_name='Alexander'
    bands=['m746','m608','m683','m710']

    def process_data(self,d):
        M746=[to_float(s) for s in d['7460']]
        M608=add_list(M746, d['6076-7460'])
        M710=add_list(M746, d['7100-7460'])
        M683=add_list(M710, d['6830-7100'])
        
        return dict([(b,locals()['M'+string.lstrip(b,'m')]) for b in self.bands])


class GCPD_Photometry_WBVR(_GCPD):
    """ WBVR photometry.
    
    
    Example:
    >>> wb=GCPD_Photometry_WBVR()
    >>> wb.bands
    ['W', 'B', 'V', 'R']
    >>> print wb.print_data('Vega',references=False) #doctest: +NORMALIZE_WHITESPACE
    # data in WBVR photometric system
    M   Vega WBVR W 0.083 0.05 # WBVR W
    M   Vega WBVR B 0.039 0.05 # WBVR B
    M   Vega WBVR V 0.028 0.05 # WBVR V
    M   Vega WBVR R 0.05 0.05 # WBVR R

    """
    system_string='WBVR'
    system_common_name='WBVR'
    bands=list('WBVR')

    def process_data(self,d):

        V=[to_float(s) for s in d['V']]
        B=add_list(V, d['B-V'])
        W=add_list(B, d['W-B'])
        R=sub_list(V, d['V-R'])
        return dict([(b,locals()[b]) for b in self.bands])



class GCPD_Photometry_Washington(_GCPD):
    """ Washington photometry
    
    
    Example:
    >>> wb=GCPD_Photometry_Washington()
    >>> wb.bands
    ['V', 'C', 'M', 'T1', 'T2']
    >>> print wb.print_data('HD142860',references=False) #doctest: +NORMALIZE_WHITESPACE
    # data in Washington photometric system
    M   HD142860 Washington V 3.85 0.05 # Washington V
    M   HD142860 Washington C 4.376 0.05 # Washington C
    M   HD142860 Washington M 3.989 0.05 # Washington M
    M   HD142860 Washington T1 3.582 0.05 # Washington T1
    M   HD142860 Washington T2 3.297 0.05 # Washington T2
    """
    system_string='Washington'
    system_common_name='Washington'
    bands=['V', 'C', 'M','T1', 'T2']  #M51?

    def process_data(self,d):
        V=[to_float(s) for s in d['V']]
        T1=sub_list(V, d['V-T1'])
        M=add_list(T1, d['M-T1'])
        C=add_list(M, d['C-M'])
        T2=sub_list(T1, d['T1-T2'])
        M51=[to_float(s) for s in d['M51']]
        return dict([(b,locals()[b]) for b in self.bands])


photo_translate_name={'(RI)Cousins':'RI_Cousins',
                      '(RI)Kron':'RI_Kron',
                      '(RI)Eggen':'RI_Eggen',
                      'UBV Cape':'UBV_Cape'
                      }
def translate_photo_name(n):
    """ translate photometry system if translation is available.
    Translated name should be easy to enter on command line."""
    if n in photo_translate_name:
        return photo_translate_name[n]
    else:
        return n
PHOTOMETRY_classes=dict([(translate_photo_name(_class.system_string),_class)
                         for name,_class in globals().items()
                         if re.match('^GCPD_Photometry', name) and type(_class)==types.ClassType])

supported_systems = PHOTOMETRY_classes.keys()

def printhelp(fd=sys.stderr):
    try :
        scriptname=__file__
    except NameError:
        scriptname='GCPD.py'
    photolist=', '.join([translate_photo_name(s) for s in supported_systems])
    print >>fd,"""Invoke this script this way:

    %(scriptname)s --target targetname --system photometry_system_name
    
    The following photometric systems are supported:

    %(photolist)s

    Th default photometric system is UBV (Johnson)

    To get the list of photometry systems for a given star, call

    %(scriptname)s --target targetname --systemlist
    
    To run the test, call %(scriptname)s --test. Net connection should be up. It is silent
    if no failures are found. Test failures are sometimes due to changing data in database.
    """ %locals()



class Usage(Exception):
    "raised any time we think users does not understand usage"
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

def main(argv=None):
    rem = ''
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help","target=","system=","test","systemlist",'rem='])
        except getopt.error, msg:
            raise Usage(msg)
        target,photosystem,systemlist=None,[],None
        for opt,val in opts:
            if opt in ['-h', '--help']:
                raise Usage('')
            if opt=='--target':
                target=val
            if opt=='--system':
                photosystem.append(val)
            if opt=='--rem':
                rem = val
            if opt in ['--test']:
                import doctest
                doctest.testmod()   
                sys.exit(0)
            if opt in ['--systemlist']:
                systemlist=True

        if target and photosystem:
            for ph in photosystem:
                if ph in PHOTOMETRY_classes:
                    cl=PHOTOMETRY_classes[ph]
                    try:
                        print cl().print_data(target,rem)
                    except IOError,k:
                        print "# IOEror ", k[0],' --- ' , k[1]
                    except StarNameException,ex:
                        print "# star %s not found"% target
                    except GCPD_No_Data,ex:
                        print "# No data for star %s in photosystem %s"% (target,photosystem)
                
        elif systemlist and target:
            try:
                l=GCPD_system_list(target)
                print "# The following photometric systems are supported for this star: ", 
                print ", ".join(l)
            except GCPD_No_Data,ex:
                print "# No supported photosystems for star %s "% target
        else:
            printhelp()
            

    except Usage, err:
        print >>sys.stderr, err.msg
        printhelp()
        return 1

if __name__ == "__main__":
    main()
