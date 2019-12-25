#!/usr/bin/env python3

##########################################################################
#
#   Peter M.U. Ung @ MSSM
#   
#   v1.0 -  14.11.18
#
#   Purpose: Do SMARTS substructure search in a supplied file
#
##########################################################################

import sys

msg = '''\n    > {0}
        [ Chemical File: sdf,smi ]
        [ SMARTS String(s) ]  ** multiple strings separated by comma
        [ Output Prefix(s) ]  ** must match the number of SMARTS 
        [ Output format: sdf,smi ]

  e.g.> x.py
          chem.sdf.bz2 
          "[NH]CC(=O)N,C[NH]C" 
          chem.glycine,chem.amine
          sdf\n'''.format(sys.argv[0])
if len(sys.argv) != 5: sys.exit(msg)

import os,re
import gzip,bz2
import pandas as pd
pd.set_option('mode.chained_assignment', None)

from rdkit import Chem
from rdkit import RDConfig
from rdkit.Chem import PandasTools as rdpd

from pathos import multiprocessing

##########################################################################
def main( filename, strings, prefixes, ext ):

  if re.search(r'\.sdf', filename):
    df = rdpd.LoadSDF( file_handle(filename), 
                       smilesName='smiles', molColName='mol',
                       includeFingerprints=True, removeHs=True )

  if re.search(r'\.smi', filename):
    with file_handle(filename) as fi:
      if re.search('smi', str(fi.readline()), re.IGNORECASE):
        print('\n # Smiles input has Header #')
        df = pd.read_csv(filename, sep='\s+', comment='#').dropna()
        df.columns = ['smiles','ID']
      else:
        print('\n # Smiles input has NO Header #')
        df = pd.read_csv(filename, header=None, sep='\s+', comment='#').dropna()
        df.columns = ['smiles','ID']
    rdpd.AddMoleculeColumnToFrame(df,'smiles','mol', includeFingerprints=True)

  print('## Number of mol read from {}: {}\n'.format(filename,len(df.smiles)))

  SMARTS   = strings.split(',')
  Prefixes = prefixes.split(',')

  substructure_match = SMARTSSearch( df=df, ext=ext )

  mpi = multiprocessing.Pool()
#  mpi.map( substructure_match, list(zip(SMARTS, Prefixes)) )
  tmp = [substructure_match(inp) for inp in list(zip(SMARTS, Prefixes))]



##########################################################################
## Match substructure with SMARTS
class SMARTSSearch(object):

  def __init__( self, df=None, ext='' ):
    self.df  = df
    self.ext = ext

  def __call__( self, inp ):
    return self.search_pattern( inp )

  def search_pattern( self, inp ):

    smarts, prefix = inp
    pattern = Chem.MolFromSmarts(smarts)

    m_df = self.df[ self.df.mol >= pattern ]
    m_df['SMARTS_Match'] = smarts

#    Matches = [m for m in self.Mols if m.HasSubstructMatch(pattern)]
    print('\n  > Molecule matching "{0}": {1}\n'.format(smarts, len(m_df)))


    if self.ext == 'sdf':
      mol_out = (prefix+'.'+self.ext)
      rdpd.WriteSDF(m_df, mol_out, molColName='mol', idName='ID',
                          properties=list(m_df.columns))

    else:
      mol_out = (prefix+'.'+self.ext)
      rdpd.SaveSMILESFromFrame(m_df, mol_out, molCol='mol', NamesCol='ID',
                                    isomericSmiles=True)



##########################################################################
## Handle gzip and bzip2 file if the extension is right. otherwise, just open
## outuput: file handle
def file_handle(file_name):
  if re.search(r'.gz$', file_name):
    handle = gzip.open(file_name, 'rb')
  elif re.search(r'.bz2$', file_name):
    handle = bz2.BZ2File(file_name, 'rb')
  else:
    handle = open(file_name, 'rb')

  return handle


#######################################################################

if __name__ == '__main__':
  main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
