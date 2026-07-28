# --- Rule 9: Safe Fuzzy Matching Keyref Upgrader (Bulletproof version) ---
        def upgrade_to_keyref(match):
            full_tag = match.group(0)
            original_href = match.group(1).strip()
            
            # 1. 
            if original_href.startswith(('http', 'mailto', 'com:', 'urn:')) or '.dita' not in original_href:
                return full_tag
                
            # 2. 
            parts = original_href.split('#')
            filepath = parts[0]
            key_name = os.path.splitext(os.path.basename(filepath))[0]
            
            # 3. 
            if len(parts) > 1:
                anchor = parts[1]
                target_id = anchor.split('/')[-1]
                
                # 
                clean_key = key_name.replace('_', '').replace('-', '').lower()
                clean_target = target_id.replace('_', '').replace('-', '').lower()
                
                is_match = False
                if clean_key == clean_target:
                    # 
                    is_match = True
                elif clean_key.startswith(clean_target) and clean_key[len(clean_target):].isdigit():
                    # 
                    is_match = True
                elif clean_target.startswith(clean_key) and clean_target[len(clean_key):].isdigit():
                    #
                    is_match = True
                
                # 
                if is_match:
                    new_attr = f'keyref="{key_name}"'
                else:
                    new_attr = f'keyref="{key_name}/{target_id}"'
            else:
                new_attr = f'keyref="{key_name}"'
                
            # 4. 
            upgraded_tag = re.sub(r'href\s*=\s*"[^"]+"', new_attr, full_tag)
            return upgraded_tag

        # 
        content = re.sub(r'<xref[^>]*?href\s*=\s*"([^"]+)"[^>]*?>', upgrade_to_keyref, content)