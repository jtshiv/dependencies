import sys
import json
import re
import subprocess

class DependencyTree:
    def __init__(self,json_data=None):
        self.packages = json_data if json_data else []
    
    def fetch_dependencies(self, package_name):
        # fetch dependencies using johnnydep to populate packages list
        try:
            result = subprocess.run(
                ["johnnydep", package_name,
                 "-f", "name", "requires",
                 "-o", "json"],
                 stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE,
                 check=True,
                 text=True
            )
            self.packages = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error fetching dependencies for {package_name}: {e.stderr}")
            sys.exit(1)
    
    def extract_req_name(self, req):
        # Regular expression to match common pip version specifiers
        specifiers = ['>=', '==', '<=', '>', '<', '~=', '!=']
        # Create a regex pattern that will split on any of the specifiers
        pattern = '|'.join(re.escape(spec) for spec in specifiers)
        return re.split(pattern, req)[0].strip().lower()
    
    def find_package(self, name):
        for package in self.packages:
            if package['name'].lower() == name.lower():
                return package
        return None
    
    def process_dependencies(self, package, indent_level=0):
        output = []
        indent = '  ' * indent_level

        output.append(f"{indent}{package['name']}")

        for req in package.get('requires', []):
            req_name = self.extract_req_name(req)
            sub_package = self.find_package(req_name)
            if sub_package:
                output.extend(self.process_dependencies(sub_package, indent_level + 1))
            else:
                output.append(f"{indent}{req}")

        return output
    
    def generate_tree(self,package_name = None):
        if not self.packages:
            if not package_name:
                print("No packages loaded and no package_name given. Ending")
                return []
            else:
                print(f"No packages loaded. Fetching {package_name} with johnnydep")
                self.fetch_dependencies(package_name)
        root_package = self.packages[0]
        self.tree = self.process_dependencies(root_package)
        return self.tree
    
    def save_to_requirements(self, file_path="requirements.txt", append=False):
        """Save the dependency tree to requirements file
         
        :param file_path: The path to the requirements file
        :param append: If True, append to the file; if False, overwrite the file.
        """
        mode = 'a' if append else 'w'
        output_lines = self.tree if self.tree else self.generate_tree()

        with open(file_path, mode) as file:
            formatted = '\n'.join(output_lines) + '\n'
            file.write(formatted)
            print(formatted)

        # Print the result to the console
        print(f"Dependency tree saved to {file_path}")
    


if __name__ == "__main__":
    file_path = None
    append = None
    if len(sys.argv) < 2:
        print("Usage: python deps.py <package_name> [filename] [--append]")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        package_name = sys.argv[1]
        file_path = sys.argv[2] if len(sys.argv) > 2 else "requirements.txt"
        append = len(sys.argv) > 3 and (sys.argv[3] == "--append" or sys.argv[3] == "-a")
        
    else:
        package_name = "pyautogui"
        file_path = "requirements.txt"
        append = True

    tree = DependencyTree()
    tree.generate_tree(package_name)

    tree.save_to_requirements(file_path,append)
    


    
    

