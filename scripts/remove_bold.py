import glob

def remove_bold():
    files = glob.glob('references/naver-blog-posting/*.md')
    count = 0
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '**' in content:
            content = content.replace('**', '')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            count += 1
            
    print(f"Successfully processed {count} files.")

if __name__ == "__main__":
    remove_bold()
