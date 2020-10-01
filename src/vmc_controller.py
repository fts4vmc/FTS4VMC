import pexpect

class vmc_controller:
    __slots__= '__vmc_instance', '__checking_outcomes', \
               '__loading_outcomes', '__checking_performed', \
               '__counterexample_enabled'

    def __init__(self,vmc):
        self.__vmc_instance = pexpect.spawn(vmc)
        self.__checking_outcomes = self.__vmc_instance.compile_pattern_list(['is: FALSE','is: TRUE'])
        self.__loading_outcomes = self.__vmc_instance.compile_pattern_list(['Error in LoadModel','Possible Evolutions'])
        self.__checking_performed = False
        self.__counterexample_enabled = False

    def __del__(self):
        self.quit()


    def load_model(self, model_path):
        
        self.__vmc_instance.expect_exact('mc>')

        self.__vmc_instance.sendline('load ' + model_path)
            
        self.__vmc_instance.expect_list(self.__loading_outcomes)
        return self.__vmc_instance.before + self.__vmc_instance.after


    def check(self, formula):
        try:
            self.__vmc_instance.expect_exact('mc>')
        except:
            return 'timeout exception'
        self.__vmc_instance.sendline(formula)
        try:
            out = self.__vmc_instance.expect_list(self.__checking_outcomes)
        except:
            return 'timeout exception'
        self.__checking_performed = True
        if out == 0:
            self.__counterexample_enabled = True
        else:
            self.__counterexample_enabled = False
        return self.__vmc_instance.before.decode("utf-8") + self.__vmc_instance.after.decode("utf-8")

    def why(self):
        if not self.__counterexample_enabled:
            if not self.__checking_performed:
                return 'Counterexample not available: no checking performed!'
            else:
                return 'Counterexample not available: the formula is TRUE'
        
        self.__vmc_instance.expect_exact('mc>')
        
        self.__vmc_instance.sendline('why')
        self.__vmc_instance.expect_exact('mc>')
        
        return self.__vmc_instance.after.decode("utf-8")  + self.__vmc_instance.before.decode("utf-8")

    def get_counterexample(self):
        why_str = self.why()
        start = why_str.find('For example:')
        end = why_str.find('is one of the above mentioned failing paths.')
        if start == -1 or end == -1 or end < start:
            return why_str 
        return why_str[start:end]
            

    def quit(self):
        self.__vmc_instance.sendline('end')

    def checking_performed(self):
        return self.__checking_performed
