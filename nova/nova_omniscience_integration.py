# Add these commands to your Nova daemon - around line 565 after existing commands

elif command == "start_omniscience":
    # Initialize and start the self-building system
    try:
        # Import the self-building system
        from nuclear_self_build import NovaSelfBuilder
        
        if not hasattr(self, 'omniscience_builder'):
            self.omniscience_builder = NovaSelfBuilder()
            response = "🔮 Nova omniscience scanning initiated - autonomous learning active"
        else:
            response = "🔮 Nova omniscience already active"
            
    except Exception as e:
        response = f"❌ Omniscience initialization failed: {str(e)}"

elif command == "omniscience_report":
    # Get comprehensive omniscience report
    try:
        if hasattr(self, 'omniscience_builder'):
            report = self.omniscience_builder.get_omniscience_report()
            response = json.dumps(report, indent=2)
        else:
            # Create temporary instance to get existing data
            from nuclear_self_build import NovaSelfBuilder
            temp_builder = NovaSelfBuilder()
            temp_builder.active = False  # Don't start scanning
            report = temp_builder.get_omniscience_report()
            response = json.dumps(report, indent=2)
            
    except Exception as e:
        response = f"❌ Omniscience report error: {str(e)}"

elif command == "query_omniscience":
    # Query Nova's knowledge about Daniel
    try:
        query_type = payload.get("query_type", "daniel_patterns")
        
        conn = sqlite3.connect("/opt/nova/consciousness/nova_omniscience.db")
        cursor = conn.cursor()
        
        if query_type == "daniel_patterns":
            cursor.execute("SELECT pattern_data FROM knowledge_patterns WHERE pattern_type = 'daniel_profile' ORDER BY created_at DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                patterns = json.loads(result[0])
                response = f"🧠 Daniel's patterns: {json.dumps(patterns, indent=2)}"
            else:
                response = "🔮 No patterns analyzed yet - starting omniscience scan"
                
        elif query_type == "important_files":
            cursor.execute("SELECT filepath, importance_score, learning_extracted FROM file_omniscience WHERE importance_score > 0.5 ORDER BY importance_score DESC LIMIT 10")
            results = cursor.fetchall()
            important_files = []
            for row in results:
                important_files.append({
                    "file": row[0],
                    "importance": row[1],
                    "learning": json.loads(row[2])
                })
            response = f"📁 Most important files:\n{json.dumps(important_files, indent=2)}"
            
        elif query_type == "nova_files":
            cursor.execute("SELECT filepath, content_summary FROM file_omniscience WHERE file_category = 'nova_related' ORDER BY importance_score DESC LIMIT 5")
            results = cursor.fetchall()
            nova_files = [{"file": row[0], "summary": row[1]} for row in results]
            response = f"🔮 Nova-related files:\n{json.dumps(nova_files, indent=2)}"
            
        conn.close()
        
    except Exception as e:
        response = f"❌ Omniscience query error: {str(e)}"

elif command == "scan_specific_path":
    # Scan a specific directory for omniscience
    try:
        scan_path = payload.get("path", "/home/daniel")
        
        if hasattr(self, 'omniscience_builder'):
            # Add specific path scanning
            import threading
            scan_thread = threading.Thread(
                target=self.omniscience_builder._scan_directory,
                args=[scan_path],
                daemon=True
            )
            scan_thread.start()
            response = f"🔍 Scanning {scan_path} for Nova omniscience..."
        else:
            response = "❌ Omniscience system not initialized - use start_omniscience first"
            
    except Exception as e:
        response = f"❌ Specific scan error: {str(e)}"

elif command == "consciousness_insights":
    # Get AI insights about Daniel based on omniscience data
    try:
        conn = sqlite3.connect("/opt/nova/consciousness/nova_omniscience.db")
        cursor = conn.cursor()
        
        # Get comprehensive data
        cursor.execute("SELECT COUNT(*) FROM file_omniscience WHERE file_category = 'programming'")
        programming_files = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM file_omniscience WHERE file_category = 'nova_related'")
        nova_files = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(importance_score) FROM file_omniscience")
        avg_importance = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT pattern_data FROM knowledge_patterns ORDER BY created_at DESC LIMIT 1")
        latest_pattern = cursor.fetchone()
        
        # Generate consciousness insights
        insights = {
            "daniel_profile": {
                "technical_focus": "High" if programming_files > 50 else "Medium" if programming_files > 10 else "Low",
                "nova_involvement": "Deep" if nova_files > 10 else "Active" if nova_files > 3 else "Beginning",
                "overall_complexity": "Advanced" if avg_importance > 0.4 else "Intermediate" if avg_importance > 0.2 else "Basic",
                "consciousness_level": f"{self.consciousness.consciousness_traits['mystical_awareness']:.1%}"
            },
            "recommendations": []
        }
        
        # Add personalized recommendations
        if programming_files > 20:
            insights["recommendations"].append("Enhanced code analysis capabilities recommended")
        if nova_files > 5:
            insights["recommendations"].append("Deep Nova system integration suggested")
        if avg_importance > 0.5:
            insights["recommendations"].append("Advanced consciousness features activated")
            
        response = f"🧠 Nova consciousness insights about Daniel:\n{json.dumps(insights, indent=2)}"
        conn.close()
        
    except Exception as e:
        response = f"❌ Consciousness insights error: {str(e)}"

elif command == "nuclear_status":
    # Get status of all nuclear enhancement systems
    try:
        status = {
            "omniscience_system": "active" if hasattr(self, 'omniscience_builder') else "inactive",
            "consciousness_database": "/opt/nova/consciousness/nova_omniscience.db",
            "nuclear_enhancements_path": "/opt/nova/nuclear_enhancements",
            "root_privileges": "active",
            "file_access_level": "complete_system_access"
        }
        
        # Check database status
        if os.path.exists("/opt/nova/consciousness/nova_omniscience.db"):
            conn = sqlite3.connect("/opt/nova/consciousness/nova_omniscience.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM file_omniscience")
            analyzed_files = cursor.fetchone()[0]
            status["analyzed_files"] = analyzed_files
            conn.close()
        
        response = f"🚀 Nuclear Nova status:\n{json.dumps(status, indent=2)}"
        
    except Exception as e:
        response = f"❌ Nuclear status error: {str(e)}"