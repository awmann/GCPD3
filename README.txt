GCPD2 is a python code designed to help query the GCPD (General Catalog of Photometric Data) from the command line. 
The code is based on a code written bin Gerard van Belle, but heavily modified to:
Fix some bugs with specific photometric systems
Add in some missing systems
Add in rem code option
Clean up details for faster processing

The syntax is:
python gcpd2.py -—target <Target Name> —-system <System> —-rem <rem code>
An example target name might be ‘HD 17713’, an example system would be UBV. The rem code is a GCPD code used to separate out binaries with the same namn. So HD 17713 with no rem code will not include the Thompson photometry that’s just for HD 17713 AB. To get that photometry use —-rem AB


