import os
import re
import subprocess

#Separator used while evaluating VMC's output
separator = '-------------------------------------------\nThe formula:' 

class VmcException(Exception):
    pass

class VmcController:
    __slots__ = ['vmc_path',
                'output',#VMC's output
                '_formula',#an UCTL formula extracted from 'properties' file passed to run_vmc(...)
                '_eval',#result of the evaluation of the current _formula
                '_details',#does the formula's evaluation holds for all the MTS' variants
                'explanation' #why is the formula FALSE?
                ]

    def __init__(self,vmc_path):
        if(not os.path.isfile(vmc_path)):
            raise ValueError('Invalid vmc_path')
        else:
            self.vmc_path = vmc_path
            self.output = ''
            self.explanation = ''
            self._formula = ''
            self._eval = ''
            self._details = ''

    #Returns True if the last formula was evaluated as TRUE by VMC
    def _is_true(self):
        idx = self.output.find('is: TRUE')
        return idx != -1

    #Returns True if the last formula's evaluation holds for all the MTS' variants
    def _holds_for_variants(self):
        idx = self.output.find('The formula holds also for all the MTS variants')
        return idx != -1

    #Returns True if the last formula's evaluation doen not hold for any of the MTS' variants
    def _holds_for_no_variant(self):
        idx = self.output.find('The formula does NOT hold for any MTS variant')
        return idx != -1
    
    #Returns True if the formula is actually an UCTL formula
    def _is_formula(self):
        idx = self.output.find('Nothing to explain! first type in an UCTL formula!')
        return idx == -1

    #model: file containing an FTS
    #properties: file containing a formula
    def run_vmc(self, model, properties):
        if(not os.path.isfile(model)):
            raise ValueError('Invalid model file')
        if(not os.path.isfile(properties)):
            raise ValueError('Invalid properties file')
        self.output = subprocess.check_output(os.path.abspath(self.vmc_path) +#Running vmc
                ' ' + model + ' ' + properties + ' +z', shell=True)
        decoded = self.output.decode("utf-8")
        if separator in decoded:
            self.output, self.explanation = decoded.split(separator,1) 
            self.explanation = separator +'\n' + self.explanation 
            if(self._is_true()):
                self.explanation = 'Nothing to show: the formula is TRUE'
        else:
            self.output = decoded

        #Checking formula
        formula = ''
        with open(properties,"r") as prop_file:
            formula = prop_file.read()

        if(not self._is_formula()):
            self._formula = formula
            self._eval = 'INVALID'
            self._details = 'Nothing to explain. The provided formula is not valid'
            self.explanation = 'Nothing to explain. The provided formula is not valid'
            return
        
        #Rewriting output
        tmp_output = ''
        tmp_output += 'The Formula: ' + formula
        if(self._is_true()):
            self._eval = 'TRUE'
            tmp_output += ' is TRUE'
        else:
            self._eval = 'FALSE'
            tmp_output += ' is FALSE'

 
        if(self._holds_for_variants()):
            self._details = 'and holds for all the MTS variants'
            tmp_output += ' and holds for all the MTS variants'
        elif(self._holds_for_no_variant()):
            self._details = 'and does NOT hold for any MTS variant'
        else:
            tmp_output += 'and, even if the formula is ' + self._eval + ' for the MTS, its validity is not necessarily preserved by the MTS variants'
            self._details = ' even if the formula is ' + self._eval + ' for the MTS, its validity is not necessarily preserved by the MTS variants'


        self.output = tmp_output
        self._formula = formula
                

    def get_formula(self):
        return self._formula

    def get_explanation(self):
        lines = '-------------------------------------------'
        return self.explanation.replace(lines, '').split('\n')

    def get_eval(self):
        return self._eval

    def get_details(self):
        return self._details

    def clean_counterexample(self):
        clean_counter = ''
        for line in self.explanation.split('\n'):
            if "-->" in line:
                #if at least an occurrence of '-->' is found we can infer
                #that the formula was evaluated as FALSE
                clean_counter = clean_counter + line + '\n'
        return clean_counter
