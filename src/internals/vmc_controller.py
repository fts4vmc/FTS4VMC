import os
import re
import subprocess

separator = '-------------------------------------------\nThe formula:' 

class VmcController:
    __slots__ = ['vmc_path','output','_formula','_eval','_details','explanation','counterexample']

    def __init__(self,vmc_path):
        if(not os.path.isfile(vmc_path)):
            raise ValueError('Invalid vmc_path')
        else:
            self.vmc_path = vmc_path
            self.output = ''
            self.explanation = ''
            self.counterexample = ''
            self._formula = ''
            self._eval = ''
            self._details = ''

    def _is_true(self):
        idx = self.output.find('is: TRUE')
        return not (idx == -1)

    def _holds_for_variants(self):
        idx = self.output.find('')
        return not (idx == -1)

    def run_vmc(self, model, properties):
        if(not os.path.isfile(model)):
            raise ValueError('Invalid model file')
        if(not os.path.isfile(properties)):
            raise ValueError('Invalid properties file')
        self.output = subprocess.check_output(self.vmc_path + ' ' + model + ' ' + properties + ' +z', shell=True)
        decoded = self.output.decode("utf-8")
        if separator in decoded:
            self.output, self.explanation = decoded.split(separator,1) 
            self.explanation = separator +'\n' + self.explanation 
            if(self._is_true()):
                self.explanation = 'Nothing to show: the formula is TRUE'
        else:
            self.output = decoded
        #Rewriting output
        formula = ''
        with open(properties,"r") as prop_file:
            formula = prop_file.read()
        tmp_output = ''
        tmp_output += 'The Formula: ' + formula
        if(self._is_true()):
            self._eval = 'TRUE'
            tmp_output += ' is TRUE'
        else:
            tmp_output += ' is FALSE.\nEven if the formula is FALSE for the MTS, its validity is not necessarily preserved by the MTS variants'

 
        if(self._holds_for_variants()):
            self._details = ' and holds for all the MTS variants'
            tmp_output += ' and holds for all the MTS variants'
        else:
            tmp_output += ' even if the formula is ' + self._eval + ' for the MTS, its validity is not necessarily preserved by the MTS variants'
            self._details = ' even if the formula is ' + self._eval + ' for the MTS, its validity is not necessarily preserved by the MTS variants'


        self.output = tmp_output
        self._formula = formula
        

    def get_output(self):
        if(self.output == ''):
            return 'Nothing to show.'
        return self.output

    def get_formula(self):
        return self._formula

    def get_eval(self):
        return self._eval

    def get_details(self):
        return self._details

    def get_explanation(self):
        if(self.explanation == ''):
            return 'Nothing to show.'
        return self.explanation
