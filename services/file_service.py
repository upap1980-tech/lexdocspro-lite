from pathlib import Path

class FileService:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
    
    def list_directory(self, path=''):
        current_dir = self.root_dir / path if path else self.root_dir
        
        if not current_dir.exists():
            return {'files': [], 'folders': []}
        
        files = []
        folders = []
        
        try:
            for item in sorted(current_dir.iterdir()):
                if item.name.startswith('.'):
                    continue
                
                rel_path = str(item.relative_to(self.root_dir))
                
                if item.is_dir():
                    folders.append({
                        'name': item.name,
                        'path': rel_path
                    })
                elif item.suffix.lower() == '.pdf':
                    files.append({
                        'name': item.name,
                        'path': rel_path,
                        'size': item.stat().st_size
                    })
        except PermissionError:
            pass
        
        return {
            'files': files,
            'folders': folders,
            'current_path': path
        }
