"""
UC4: Duplicate Records Detection and Resolution System

This module contains multiple specialized agents for detecting and resolving duplicate records.
Each agent focuses on a specific aspect of duplicate detection using Agno framework with Azure OpenAI.

Agents included:
1. ExactDuplicateDetectionAgent - Exact row-level duplicate detection
2. SemanticDuplicateAgent - Fuzzy/semantic duplicate detection  
3. BusinessKeyDuplicateAgent - Business rule-based duplicate detection
4. DeduplicationStrategyAgent - Duplicate resolution strategies
5. UC4OrchestrationAgent - Coordinates all UC4 agents
"""

import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime
import json
import hashlib

from agno.agent import Agent
from agno.tools.file import FileTools
from agno.tools.python import PythonTools
from agno.tools.reasoning import ReasoningTools

from .base_config import AgentConfig, BaseAgentResults, log_agent_activity


class ExactDuplicateDetectionAgent:
    """
    Agent specialized in detecting exact duplicate rows in datasets.
    Uses precise row-level comparison and hash-based duplicate detection.
    """
    
    def __init__(self):
        self.agent_name = "UC4_ExactDuplicateDetectionAgent"
        self.config = AgentConfig()
        
        self.agent = Agent(
            name="Exact Duplicate Detection Specialist",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                FileTools(),
                PythonTools(run_code=True, uv_pip_install=False,),
                ReasoningTools(add_instructions=True)
            ],
            instructions=[
                "You are an EXACT DUPLICATE DETECTION SPECIALIST with expertise in identifying identical records in datasets.",
                "",
                "CORE SPECIALIZATION:",
                "- Detect rows that are completely identical across all fields",
                "- Identify partial duplicates (subset of columns matching)",
                "- Calculate duplicate frequency and distribution patterns",
                "- Assess data quality impact from duplicate records",
                "",
                "DETECTION METHODOLOGY:",
                "• EXACT ROW DUPLICATES: All column values identical",
                "• HASH-BASED DETECTION: Use cryptographic hashing for efficiency",
                "• COLUMN SUBSET DUPLICATES: Key business fields identical",
                "• FREQUENCY ANALYSIS: Count occurrences and patterns",
                "",
                "DUPLICATE CATEGORIES:",
                "1. Complete Row Duplicates: 100% identical across all columns",
                "2. Business Key Duplicates: Critical business fields identical",
                "3. Content Duplicates: Core content fields identical",
                "4. Near-Miss Duplicates: Almost identical with minor variations",
                "",
                "IMPACT ASSESSMENT:",
                "- Data storage efficiency concerns",
                "- Statistical analysis accuracy impact",
                "- Business process duplication issues",
                "- Compliance and audit trail concerns",
                "",
                "Always provide specific row indices for detected duplicates and clear removal/deduplication strategies."
            ],
            add_datetime_to_instructions=True,
            markdown=True,
            debug_mode=True
        )
    
    async def detect_exact_duplicates(self, file_path: str) -> Dict[str, Any]:
        """
        Detect exact duplicate rows in the dataset
        
        Args:
            file_path: Path to the CSV file to analyze
            
        Returns:
            Dictionary containing exact duplicate analysis
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting exact duplicate detection", {"file": file_path})
        
        try:
            analysis_prompt = f"""
            Perform COMPREHENSIVE EXACT DUPLICATE DETECTION for file: {file_path}
            
            DETECTION REQUIREMENTS:
            
            1. **COMPLETE ROW DUPLICATE ANALYSIS**:
               - Load CSV file and identify completely identical rows
               - Calculate row hashes for efficient duplicate detection
               - Count total duplicate records and unique duplicated rows
               - Analyze duplicate frequency distribution
            
            2. **DUPLICATE PATTERN ANALYSIS**:
               - Identify most frequently duplicated records
               - Analyze spatial distribution of duplicates in dataset
               - Detect consecutive duplicate blocks vs scattered duplicates
               - Examine if duplicates correlate with specific data sections
            
            3. **FIELD-LEVEL DUPLICATE CONTRIBUTION**:
               - Identify which fields/columns contribute most to duplication
               - Analyze if duplicates are driven by specific field combinations
               - Detect null/empty field patterns in duplicate records
            
            4. **BUSINESS IMPACT ASSESSMENT**:
               - Calculate storage overhead from duplicate records
               - Assess impact on data processing performance
               - Evaluate effect on analytical accuracy and reporting
               - Identify compliance and data governance implications
            
            5. **DEDUPLICATION STRATEGY RECOMMENDATIONS**:
               - Recommend immediate removal candidates (safe duplicates)
               - Identify duplicates requiring manual review
               - Suggest automated deduplication rules
               - Provide data source improvement recommendations
            
            EXPECTED OUTPUT FORMAT:
            ```json
            {{
                "duplicate_summary": {{
                    "total_records": number,
                    "unique_records": number,
                    "duplicate_records": number,
                    "duplication_rate_percentage": number,
                    "unique_duplicated_rows": number
                }},
                "duplicate_patterns": {{
                    "most_frequent_duplicates": [
                        {{
                            "record_hash": "hash_value",
                            "duplicate_count": number,
                            "sample_row_indices": [list_of_indices],
                            "fields_summary": "key identifying information"
                        }}
                    ],
                    "duplicate_distribution": {{
                        "consecutive_blocks": number,
                        "scattered_duplicates": number,
                        "clustered_sections": ["descriptions"]
                    }}
                }},
                "field_analysis": {{
                    "high_duplication_fields": ["field names contributing most to duplicates"],
                    "duplicate_driving_combinations": ["field combinations that create duplicates"],
                    "null_patterns_in_duplicates": "analysis of null patterns"
                }},
                "business_impact": {{
                    "storage_waste_percentage": number,
                    "processing_overhead_estimate": "performance impact assessment",
                    "accuracy_degradation_risk": "high|medium|low",
                    "compliance_concerns": ["list of potential issues"]
                }},
                "deduplication_recommendations": {{
                    "immediate_removal": {{
                        "safe_duplicate_count": number,
                        "recommended_action": "automatic removal strategy"
                    }},
                    "manual_review": {{
                        "complex_duplicate_count": number,
                        "review_criteria": "what requires manual attention"
                    }},
                    "prevention_strategies": [
                        "data source improvements to prevent future duplicates"
                    ]
                }}
            }}
            ```
            
            Use Python tools to perform actual duplicate detection algorithms. Provide specific row indices for samples.
            """
            
            response = self.agent.run(analysis_prompt)
            
            results = BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                analysis_type="exact_duplicate_detection",
                agent_response=response.content if hasattr(response, 'content') else str(response),
                analysis_focus="Complete row-level exact duplicate detection and analysis"
            )
            
            log_agent_activity(self.agent_name, "Exact duplicate detection completed", 
                             {"execution_time_ms": results["execution_time_ms"]})
            
            return results
            
        except Exception as e:
            log_agent_activity(self.agent_name, "Detection failed", {"error": str(e)})
            return BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                success=False,
                error=str(e)
            )


class SemanticDuplicateAgent:
    """
    Agent specialized in detecting semantic/fuzzy duplicates using similarity algorithms.
    Focuses on records that are similar but not exactly identical.
    """
    
    def __init__(self):
        self.agent_name = "UC4_SemanticDuplicateAgent"
        self.config = AgentConfig()
        
        self.agent = Agent(
            name="Semantic Duplicate Detection Expert",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                FileTools(),
                PythonTools(run_code=True, uv_pip_install=False,),
                ReasoningTools(add_instructions=True)
            ],
            instructions=[
                "You are a SEMANTIC DUPLICATE DETECTION EXPERT specializing in finding similar but not identical records.",
                "",
                "SEMANTIC DETECTION EXPERTISE:",
                "- Identify records that are similar but have minor variations",
                "- Detect fuzzy duplicates using string similarity algorithms",
                "- Find records with formatting differences but same semantic meaning",
                "- Analyze near-duplicate patterns and similarity thresholds",
                "",
                "SIMILARITY DETECTION METHODS:",
                "1. String similarity (Levenshtein, Jaro-Winkler, Jaccard)",
                "2. Phonetic similarity (Soundex, Metaphone)",
                "3. Token-based similarity (overlapping words/tokens)",
                "4. Normalized field comparison (case, whitespace, punctuation)",
                "5. Business rule-based semantic matching",
                "",
                "SIMILARITY CATEGORIES:",
                "• HIGH SIMILARITY (>90%): Likely same entity with minor variations",
                "• MEDIUM SIMILARITY (70-90%): Potential duplicates requiring review",
                "• LOW SIMILARITY (50-70%): Possible related records",
                "• WEAK SIMILARITY (<50%): Unlikely to be duplicates",
                "",
                "FUZZY DUPLICATE PATTERNS:",
                "- Formatting variations (spaces, case, punctuation)",
                "- Abbreviations vs full forms",
                "- Typos and spelling variations",
                "- Field order differences",
                "- Partial information vs complete records",
                "",
                "BUSINESS SCENARIOS:",
                "- Customer name variations (John Smith vs J. Smith)",
                "- Address formatting differences",
                "- Product description variations",
                "- Company name abbreviations",
                "",
                "Always provide similarity scores and recommend human review thresholds for ambiguous cases."
            ],
            add_datetime_to_instructions=True,
            markdown=True,
            debug_mode=True
        )
    
    async def detect_semantic_duplicates(self, file_path: str, similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Detect semantic/fuzzy duplicate records
        
        Args:
            file_path: Path to the CSV file to analyze
            similarity_threshold: Minimum similarity score to consider as duplicate (default 0.8)
            
        Returns:
            Dictionary containing semantic duplicate analysis
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting semantic duplicate detection", 
                         {"file": file_path, "similarity_threshold": similarity_threshold})
        
        try:
            analysis_prompt = f"""
            Perform ADVANCED SEMANTIC DUPLICATE DETECTION for file: {file_path}
            
            ANALYSIS PARAMETERS:
            - Similarity threshold: {similarity_threshold} ({similarity_threshold*100}% similarity required)
            - Focus: Fuzzy duplicates and semantic similarity
            
            DETECTION REQUIREMENTS:
            
            1. **MULTI-ALGORITHM SIMILARITY ANALYSIS**:
               - Apply string similarity algorithms (Levenshtein distance, Jaro-Winkler)
               - Use token-based similarity for multi-word fields
               - Implement phonetic matching for name-like fields
               - Calculate composite similarity scores across multiple fields
            
            2. **FIELD-SPECIFIC SIMILARITY STRATEGIES**:
               - Text fields: Use fuzzy string matching with normalization
               - Numeric fields: Use range-based similarity
               - Date fields: Use temporal proximity analysis
               - Categorical fields: Use exact matching with synonyms
            
            3. **SIMILARITY PATTERN ANALYSIS**:
               - Identify common types of variations (formatting, abbreviations, typos)
               - Cluster similar records by similarity patterns
               - Analyze threshold sensitivity (how results change with different thresholds)
               - Detect systematic vs random variations
            
            4. **BUSINESS CONTEXT EVALUATION**:
               - Prioritize similarity in business-critical fields
               - Apply domain-specific similarity rules
               - Consider field importance weighting
               - Assess business impact of each potential duplicate group
            
            5. **CONFIDENCE SCORING AND RECOMMENDATIONS**:
               - Assign confidence levels to each potential duplicate pair
               - Recommend automatic resolution vs manual review
               - Suggest field-specific normalization strategies
               - Provide similarity threshold optimization recommendations
            
            EXPECTED OUTPUT FORMAT:
            ```json
            {{
                "semantic_analysis_summary": {{
                    "similarity_threshold_used": {similarity_threshold},
                    "potential_duplicate_pairs": number,
                    "high_confidence_duplicates": number,
                    "manual_review_candidates": number,
                    "false_positive_estimate": number
                }},
                "similarity_distribution": {{
                    "very_high_similarity_90_plus": number,
                    "high_similarity_80_90": number,
                    "medium_similarity_70_80": number,
                    "low_similarity_below_70": number
                }},
                "duplicate_groups": [
                    {{
                        "group_id": number,
                        "similarity_score": number,
                        "confidence_level": "high|medium|low",
                        "record_indices": [list_of_row_indices],
                        "similarity_type": "formatting|abbreviation|typo|other",
                        "key_differences": ["list of main differences"],
                        "recommended_action": "auto_merge|manual_review|keep_separate",
                        "business_impact": "high|medium|low"
                    }}
                ],
                "pattern_analysis": {{
                    "common_variation_types": ["most frequent types of differences"],
                    "problematic_fields": ["fields with most fuzzy duplicates"],
                    "systematic_patterns": ["repeating patterns in variations"]
                }},
                "optimization_recommendations": {{
                    "threshold_sensitivity": "analysis of how threshold affects results",
                    "field_normalization_suggestions": ["data cleaning recommendations"],
                    "algorithm_performance": "which similarity methods work best for this data",
                    "business_rule_suggestions": ["domain-specific matching rules to implement"]
                }}
            }}
            ```
            
            Use Python tools to implement actual similarity algorithms. Consider computational efficiency for large datasets.
            """
            
            response = self.agent.run(analysis_prompt)
            
            results = BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                analysis_type="semantic_duplicate_detection",
                similarity_threshold=similarity_threshold,
                agent_response=response.content if hasattr(response, 'content') else str(response),
                analysis_focus="Fuzzy duplicate detection using semantic similarity algorithms"
            )
            
            log_agent_activity(self.agent_name, "Semantic duplicate detection completed", 
                             {"execution_time_ms": results["execution_time_ms"]})
            
            return results
            
        except Exception as e:
            log_agent_activity(self.agent_name, "Detection failed", {"error": str(e)})
            return BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                success=False,
                error=str(e)
            )


class BusinessKeyDuplicateAgent:
    """
    Agent specialized in detecting duplicates based on business rules and key field combinations.
    Focuses on domain-specific duplicate detection logic.
    """
    
    def __init__(self):
        self.agent_name = "UC4_BusinessKeyDuplicateAgent"
        self.config = AgentConfig()
        
        self.agent = Agent(
            name="Business Key Duplicate Detection Specialist",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                FileTools(read_files=True, save_files=True),
                PythonTools(run_code=True, uv_pip_install=False,),
                ReasoningTools(add_instructions=True)
            ],
            instructions=[
                "You are a BUSINESS KEY DUPLICATE DETECTION SPECIALIST with expertise in domain-specific duplicate identification.",
                "",
                "BUSINESS-FOCUSED DUPLICATE DETECTION:",
                "- Identify duplicates based on business key combinations",
                "- Apply domain-specific business rules for duplicate detection",
                "- Detect logical duplicates that may differ in non-key fields",
                "- Analyze business constraint violations and data integrity issues",
                "",
                "KEY IDENTIFICATION STRATEGIES:",
                "1. Primary business identifiers (IDs, codes, reference numbers)",
                "2. Natural keys (name + date, email, phone)",
                "3. Composite keys (multiple field combinations)",
                "4. Hierarchical keys (parent-child relationships)",
                "5. Context-dependent keys (domain-specific combinations)",
                "",
                "BUSINESS RULE FRAMEWORKS:",
                "• STRICT BUSINESS KEYS: Must be unique (ID numbers, barcodes)",
                "• LOGICAL DUPLICATES: Same entity with different attributes",
                "• TEMPORAL DUPLICATES: Same entity at different time points",
                "• HIERARCHICAL DUPLICATES: Related entities in hierarchy",
                "",
                "DOMAIN-SPECIFIC PATTERNS:",
                "- Customer data: Name + Address, Email, Phone combinations",
                "- Product data: SKU, Barcode, Name + Category combinations",
                "- Transaction data: Transaction ID, Reference Number uniqueness",
                "- Employee data: Employee ID, Email, SSN uniqueness",
                "",
                "BUSINESS IMPACT ANALYSIS:",
                "- Regulatory compliance violations",
                "- Financial accuracy and audit concerns",
                "- Customer experience degradation",
                "- Operational efficiency impacts",
                "",
                "RESOLUTION PRIORITIZATION:",
                "- Critical business constraint violations (highest priority)",
                "- Financial impact duplicates (high priority)",
                "- Customer-facing duplicates (medium-high priority)",
                "- Internal process duplicates (medium priority)",
                "",
                "Always provide business justification for duplicate detection rules and resolution priorities."
            ],
            add_datetime_to_instructions=True,
            markdown=True,
            debug_mode=True
        )
    
    async def detect_business_key_duplicates(self, file_path: str) -> Dict[str, Any]:
        """
        Detect duplicates based on business keys and domain rules
        
        Args:
            file_path: Path to the CSV file to analyze
            
        Returns:
            Dictionary containing business key duplicate analysis
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting business key duplicate detection", {"file": file_path})
        
        try:
            analysis_prompt = f"""
            Perform COMPREHENSIVE BUSINESS KEY DUPLICATE DETECTION for file: {file_path}
            
            BUSINESS ANALYSIS REQUIREMENTS:
            
            1. **BUSINESS KEY IDENTIFICATION**:
               - Analyze dataset structure to identify potential business keys
               - Detect primary identifiers (IDs, codes, reference numbers)
               - Identify natural key combinations (name+date, email, etc.)
               - Examine field patterns to infer business significance
            
            2. **DOMAIN-SPECIFIC RULE APPLICATION**:
               - Apply standard business uniqueness constraints
               - Detect violations of logical business rules
               - Identify context-dependent duplicate patterns
               - Analyze temporal aspects of potential duplicates
            
            3. **KEY COMBINATION ANALYSIS**:
               - Test various field combinations for uniqueness violations
               - Identify minimal key sets that should be unique
               - Detect composite key duplicates
               - Analyze hierarchical relationship duplicates
            
            4. **BUSINESS CONSTRAINT VALIDATION**:
               - Check for violations of business uniqueness rules
               - Identify regulatory compliance issues
               - Detect financial accuracy concerns
               - Analyze customer data integrity problems
            
            5. **IMPACT AND PRIORITIZATION ASSESSMENT**:
               - Categorize duplicates by business impact severity
               - Assess regulatory and compliance implications
               - Evaluate financial and operational consequences
               - Prioritize resolution efforts by business criticality
            
            EXPECTED OUTPUT FORMAT:
            ```json
            {{
                "business_key_analysis": {{
                    "identified_primary_keys": ["field names that appear to be primary keys"],
                    "natural_key_combinations": ["field combinations that should be unique"],
                    "composite_keys": ["multi-field business key combinations"],
                    "business_constraints_found": ["inferred business rules"]
                }},
                "duplicate_violations": {{
                    "primary_key_violations": {{
                        "count": number,
                        "severity": "critical|high|medium|low",
                        "affected_keys": ["specific key values with duplicates"],
                        "business_impact": "description of impact"
                    }},
                    "natural_key_violations": {{
                        "count": number,
                        "key_combinations": ["specific combinations with duplicates"],
                        "pattern_analysis": "description of violation patterns"
                    }},
                    "composite_key_violations": {{
                        "count": number,
                        "affected_combinations": ["field combination details"],
                        "business_logic_implications": "what these violations mean"
                    }}
                }},
                "domain_specific_findings": {{
                    "customer_duplicates": "if customer data detected",
                    "product_duplicates": "if product data detected",
                    "transaction_duplicates": "if transaction data detected",
                    "reference_data_duplicates": "if reference/lookup data detected"
                }},
                "business_impact_assessment": {{
                    "regulatory_compliance_risk": "high|medium|low",
                    "financial_accuracy_risk": "high|medium|low",
                    "operational_efficiency_impact": "high|medium|low",
                    "customer_experience_impact": "high|medium|low"
                }},
                "resolution_strategy": {{
                    "critical_priority": [
                        {{
                            "duplicate_type": "description",
                            "resolution_action": "specific action needed",
                            "business_justification": "why this is critical",
                            "estimated_effort": "time/resource estimate"
                        }}
                    ],
                    "high_priority": ["medium-term resolution actions"],
                    "medium_priority": ["longer-term improvement actions"],
                    "monitoring_requirements": ["ongoing checks needed"]
                }}
            }}
            ```
            
            Use Python tools to analyze actual data patterns and business key violations. Focus on business logic and domain expertise.
            """
            
            response = self.agent.run(analysis_prompt)
            
            results = BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                analysis_type="business_key_duplicate_detection",
                agent_response=response.content if hasattr(response, 'content') else str(response),
                analysis_focus="Business rule-based duplicate detection and constraint validation"
            )
            
            log_agent_activity(self.agent_name, "Business key duplicate detection completed", 
                             {"execution_time_ms": results["execution_time_ms"]})
            
            return results
            
        except Exception as e:
            log_agent_activity(self.agent_name, "Detection failed", {"error": str(e)})
            return BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                success=False,
                error=str(e)
            )


class DeduplicationStrategyAgent:
    """
    Agent specialized in developing and recommending deduplication strategies and resolution approaches.
    Focuses on practical implementation of duplicate resolution.
    """
    
    def __init__(self):
        self.agent_name = "UC4_DeduplicationStrategyAgent"
        self.config = AgentConfig()
        
        self.agent = Agent(
            name="Deduplication Strategy Expert",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                FileTools(),
                PythonTools(run_code=True, uv_pip_install=False,),
                ReasoningTools(add_instructions=True)
            ],
            instructions=[
                "You are a DEDUPLICATION STRATEGY EXPERT specializing in developing practical duplicate resolution approaches.",
                "",
                "STRATEGIC DEDUPLICATION EXPERTISE:",
                "- Develop comprehensive deduplication strategies and workflows",
                "- Design automated and manual resolution processes",
                "- Create data quality improvement roadmaps",
                "- Optimize deduplication for different business scenarios",
                "",
                "RESOLUTION STRATEGY FRAMEWORKS:",
                "1. Automated resolution (safe, rule-based removal)",
                "2. Semi-automated resolution (algorithm + human review)",
                "3. Manual resolution (complex cases requiring judgment)",
                "4. Preventive strategies (future duplicate prevention)",
                "5. Monitoring and maintenance (ongoing quality assurance)",
                "",
                "DEDUPLICATION APPROACHES:",
                "• DELETION: Remove obviously redundant duplicate records",
                "• MERGING: Combine information from multiple duplicate records",
                "• FLAGGING: Mark duplicates for business user review",
                "• ARCHIVING: Move duplicates to separate archive for audit",
                "",
                "BUSINESS SCENARIO STRATEGIES:",
                "- High-volume transactional data (efficiency-focused)",
                "- Customer master data (accuracy-focused)",
                "- Financial records (compliance-focused)",
                "- Product catalogs (consistency-focused)",
                "",
                "IMPLEMENTATION CONSIDERATIONS:",
                "- Data backup and recovery procedures",
                "- Audit trail and change tracking",
                "- Performance impact on systems",
                "- User training and change management",
                "- Rollback procedures for incorrect deduplication",
                "",
                "QUALITY ASSURANCE:",
                "- Pre-deduplication validation checks",
                "- Post-deduplication quality verification",
                "- Exception handling and edge cases",
                "- Continuous monitoring and improvement",
                "",
                "Always provide detailed implementation plans with risk mitigation strategies."
            ],
            add_datetime_to_instructions=True,
            markdown=True,
            debug_mode=True
        )
    
    async def develop_deduplication_strategy(self, file_path: str,
                                           exact_duplicates: Dict = None,
                                           semantic_duplicates: Dict = None,
                                           business_duplicates: Dict = None) -> Dict[str, Any]:
        """
        Develop comprehensive deduplication strategy based on duplicate analysis results
        
        Args:
            file_path: Path to the CSV file to analyze
            exact_duplicates: Results from ExactDuplicateDetectionAgent
            semantic_duplicates: Results from SemanticDuplicateAgent
            business_duplicates: Results from BusinessKeyDuplicateAgent
            
        Returns:
            Dictionary containing deduplication strategy and implementation plan
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting deduplication strategy development", {"file": file_path})
        
        try:
            # Prepare analysis context
            analysis_context = {
                "exact_duplicates": exact_duplicates or {},
                "semantic_duplicates": semantic_duplicates or {},
                "business_duplicates": business_duplicates or {}
            }
            
            strategy_prompt = f"""
            Develop COMPREHENSIVE DEDUPLICATION STRATEGY AND IMPLEMENTATION PLAN for file: {file_path}
            
            AVAILABLE DUPLICATE ANALYSIS RESULTS:
            {json.dumps(analysis_context, indent=2, default=str)}
            
            STRATEGY DEVELOPMENT REQUIREMENTS:
            
            1. **DUPLICATE CATEGORIZATION AND PRIORITIZATION**:
               - Categorize all detected duplicates by resolution complexity
               - Prioritize duplicates by business impact and resolution urgency
               - Assess risk levels for different deduplication approaches
               - Create resolution decision matrix
            
            2. **AUTOMATED RESOLUTION STRATEGY**:
               - Identify duplicates safe for automated removal
               - Design rule-based automated deduplication algorithms
               - Specify conditions and constraints for automatic processing
               - Calculate expected automation success rates
            
            3. **MANUAL REVIEW PROCESS DESIGN**:
               - Define criteria for manual review requirements
               - Design human review workflows and interfaces
               - Create decision support tools for reviewers
               - Establish quality assurance checkpoints
            
            4. **IMPLEMENTATION ROADMAP**:
               - Phase deduplication implementation by complexity and risk
               - Design pilot program for testing deduplication approaches
               - Plan full-scale rollout with risk mitigation
               - Establish rollback procedures and safety measures
            
            5. **QUALITY ASSURANCE AND MONITORING**:
               - Design pre-deduplication validation procedures
               - Create post-deduplication quality verification
               - Establish ongoing duplicate monitoring systems
               - Plan continuous improvement feedback loops
            
            6. **BUSINESS IMPACT AND CHANGE MANAGEMENT**:
               - Assess business process impacts of deduplication
               - Design user training and communication plans
               - Plan for system performance optimization
               - Create business value measurement framework
            
            EXPECTED OUTPUT FORMAT:
            ```json
            {{
                "strategy_overview": {{
                    "total_duplicates_identified": number,
                    "automated_resolution_candidates": number,
                    "manual_review_candidates": number,
                    "complex_cases_requiring_business_input": number,
                    "estimated_data_quality_improvement": "percentage improvement expected"
                }},
                "resolution_approach": {{
                    "automated_deletion": {{
                        "candidate_count": number,
                        "safety_criteria": ["conditions that must be met"],
                        "risk_level": "low|medium|high",
                        "implementation_steps": ["step-by-step process"]
                    }},
                    "automated_merging": {{
                        "candidate_count": number,
                        "merge_rules": ["specific rules for combining records"],
                        "conflict_resolution": ["how to handle field conflicts"],
                        "validation_checks": ["post-merge validation procedures"]
                    }},
                    "manual_review_workflow": {{
                        "review_queue_size": number,
                        "reviewer_tools_needed": ["tools and interfaces required"],
                        "decision_criteria": ["guidelines for manual decisions"],
                        "escalation_procedures": ["complex case handling"]
                    }}
                }},
                "implementation_phases": {{
                    "phase_1_pilot": {{
                        "duration": "time estimate",
                        "scope": "subset of data for testing",
                        "success_criteria": ["measurable pilot success metrics"],
                        "rollback_plan": "how to undo if issues occur"
                    }},
                    "phase_2_automated": {{
                        "duration": "time estimate",
                        "scope": "automated resolution implementation",
                        "resource_requirements": ["technical and human resources needed"],
                        "monitoring_plan": ["how to monitor automated processes"]
                    }},
                    "phase_3_manual_review": {{
                        "duration": "time estimate",
                        "scope": "manual review process implementation",
                        "training_requirements": ["user training and change management"],
                        "quality_assurance": ["QA procedures for manual reviews"]
                    }},
                    "phase_4_optimization": {{
                        "duration": "time estimate",
                        "scope": "process optimization and continuous improvement",
                        "performance_tuning": ["system and process improvements"],
                        "feedback_integration": ["how to incorporate lessons learned"]
                    }}
                }},
                "risk_mitigation": {{
                    "data_loss_prevention": ["safeguards against accidental data loss"],
                    "business_disruption_minimization": ["how to minimize operational impact"],
                    "quality_regression_prevention": ["how to prevent quality degradation"],
                    "rollback_procedures": ["detailed rollback and recovery procedures"]
                }},
                "success_metrics": {{
                    "quantitative_metrics": ["measurable success indicators"],
                    "qualitative_metrics": ["business value indicators"],
                    "monitoring_dashboards": ["ongoing monitoring requirements"],
                    "reporting_framework": ["regular reporting and review processes"]
                }},
                "long_term_prevention": {{
                    "data_source_improvements": ["upstream data quality improvements"],
                    "process_changes": ["business process modifications"],
                    "technology_solutions": ["technical solutions for prevention"],
                    "governance_framework": ["data governance improvements"]
                }}
            }}
            ```
            
            If duplicate analysis results are not provided, perform basic analysis first. Focus on practical, implementable strategies.
            """
            
            response = self.agent.run(strategy_prompt)
            
            results = BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                analysis_type="deduplication_strategy_development",
                input_analyses=analysis_context,
                agent_response=response.content if hasattr(response, 'content') else str(response),
                analysis_focus="Comprehensive deduplication strategy and implementation planning"
            )
            
            log_agent_activity(self.agent_name, "Deduplication strategy development completed", 
                             {"execution_time_ms": results["execution_time_ms"]})
            
            return results
            
        except Exception as e:
            log_agent_activity(self.agent_name, "Strategy development failed", {"error": str(e)})
            return BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                success=False,
                error=str(e)
            )


class UC4OrchestrationAgent:
    """
    Orchestration agent that coordinates all UC4 duplicate detection agents and provides unified results.
    This agent manages the workflow and synthesizes insights from all other UC4 agents.
    """
    
    def __init__(self):
        self.agent_name = "UC4_OrchestrationAgent"
        self.config = AgentConfig()
        
        # Initialize all specialized agents
        self.exact_duplicate_agent = ExactDuplicateDetectionAgent()
        self.semantic_duplicate_agent = SemanticDuplicateAgent()
        self.business_key_agent = BusinessKeyDuplicateAgent()
        self.deduplication_strategy_agent = DeduplicationStrategyAgent()
        
        self.agent = Agent(
            name="UC4 Duplicate Detection Orchestrator",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                ReasoningTools(add_instructions=True)
            ],
            instructions=[
                "You are the UC4 ORCHESTRATION AGENT responsible for coordinating comprehensive duplicate detection and resolution.",
                "",
                "ORCHESTRATION RESPONSIBILITIES:",
                "- Coordinate execution of all specialized UC4 duplicate detection agents",
                "- Synthesize results from multiple detection approaches into unified insights",
                "- Resolve conflicts or overlaps between different duplicate detection methods",
                "- Provide executive summary of complete UC4 duplicate analysis",
                "",
                "AGENT COORDINATION WORKFLOW:",
                "1. ExactDuplicateDetectionAgent: Exact row-level duplicate detection",
                "2. SemanticDuplicateAgent: Fuzzy/semantic similarity detection",
                "3. BusinessKeyDuplicateAgent: Business rule-based duplicate detection",
                "4. DeduplicationStrategyAgent: Comprehensive resolution strategy",
                "5. Synthesis: Unified insights and strategic implementation guidance",
                "",
                "SYNTHESIS CAPABILITIES:",
                "- Cross-validate findings between different detection methods",
                "- Identify overlaps and gaps in duplicate detection coverage",
                "- Resolve conflicts between different agent recommendations",
                "- Prioritize duplicates based on combined analysis insights",
                "- Generate executive-level duplicate management strategy",
                "",
                "OUTPUT INTEGRATION:",
                "- Unified duplicate detection assessment",
                "- Consolidated deduplication recommendations with clear prioritization",
                "- Cross-method insights and pattern recognition",
                "- Strategic roadmap for duplicate resolution implementation",
                "",
                "BUSINESS DECISION SUPPORT:",
                "- Cost-benefit analysis of deduplication efforts",
                "- Risk assessment for different resolution approaches",
                "- Resource allocation recommendations",
                "- Timeline and milestone planning",
                "",
                "Always ensure all detection findings are properly integrated and resolution strategies are practical and implementable."
            ],
            add_datetime_to_instructions=True,
            markdown=True,
            debug_mode=True
        )
    
    async def analyze_duplicates_with_reference(self, file_path: str, reference_file_path: str = None) -> Dict[str, Any]:
        """
        Analyze file duplicates with optional reference file comparison
        
        Args:
            file_path: Path to the file to analyze
            reference_file_path: Optional path to reference file for comparison
            
        Returns:
            Dictionary containing duplicate analysis results with reference comparison
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting reference duplicate comparison", 
                         {"file": file_path, "reference": reference_file_path})
        
        try:
            if reference_file_path:
                # Perform comparative duplicate analysis against reference
                comparison_prompt = f"""
                Perform COMPARATIVE DUPLICATE ANALYSIS:
                
                Target file: {file_path}
                Reference file: {reference_file_path}
                
                COMPARISON REQUIREMENTS:
                
                1. **DUPLICATE BASELINE COMPARISON**:
                   - Compare duplicate levels between target and reference files
                   - Identify if target has more duplicates than reference
                   - Calculate relative duplicate increase/decrease
                
                2. **DUPLICATE PATTERN COMPARISON**:
                   - Compare types of duplicates (exact vs semantic vs business key)
                   - Identify new duplicate patterns in target not in reference
                   - Assess duplicate quality degradation from reference baseline
                
                3. **REFERENCE-BASED RECOMMENDATIONS**:
                   - Provide recommendations based on reference file quality
                   - Suggest bringing target file to reference quality level
                   - Identify specific improvement areas vs reference
                
                Expected output should include:
                - has_duplicates: boolean
                - duplicates_count: number
                - duplicate_increase_from_reference: percentage
                - recommendation: specific actions to match reference quality
                """
                
                response = self.agent.run(comparison_prompt)
                
                # Also run standard analysis
                standard_results = await self.run_complete_uc4_analysis(file_path)
                
                # Combine results
                results = {
                    **standard_results,
                    "reference_comparison": response.content if hasattr(response, 'content') else str(response),
                    "reference_file_path": reference_file_path,
                    "has_reference": True
                }
                
            else:
                # Standard analysis without reference
                results = await self.run_complete_uc4_analysis(file_path)
                results["has_reference"] = False
            
            log_agent_activity(self.agent_name, "Reference duplicate comparison completed", 
                             {"execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000})
            
            return results
            
        except Exception as e:
            log_agent_activity(self.agent_name, "Reference duplicate comparison failed", {"error": str(e)})
            return BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                success=False,
                error=str(e)
            )

    async def detect_duplicates(self, file_path: str) -> Dict[str, Any]:
        """
        Detect duplicates in a file (alias for backward compatibility)
        """
        return await self.run_complete_uc4_analysis(file_path)
    
    async def run_complete_uc4_analysis(self, file_path: str, 
                                      similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Run complete UC4 duplicate detection analysis using all specialized agents
        
        Args:
            file_path: Path to the CSV file to analyze
            similarity_threshold: Threshold for semantic duplicate detection
            
        Returns:
            Dictionary containing unified UC4 analysis results
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting complete UC4 analysis", 
                         {"file": file_path, "similarity_threshold": similarity_threshold})
        
        try:
            # Step 1: Run all specialized detection agents
            print(f"[UC4 Orchestrator] Running specialized agents for: {file_path}")
            
            # Execute detection agents in logical order
            exact_results = await self.exact_duplicate_agent.detect_exact_duplicates(file_path)
            semantic_results = await self.semantic_duplicate_agent.detect_semantic_duplicates(file_path, similarity_threshold)
            business_results = await self.business_key_agent.detect_business_key_duplicates(file_path)
            strategy_results = await self.deduplication_strategy_agent.develop_deduplication_strategy(
                file_path, exact_results, semantic_results, business_results
            )
            
            # Step 2: Synthesize results using orchestration agent
            synthesis_prompt = f"""
            SYNTHESIZE COMPLETE UC4 DUPLICATE DETECTION AND RESOLUTION ANALYSIS
            
            File analyzed: {file_path}
            Analysis timestamp: {start_time.isoformat()}
            
            SPECIALIZED AGENT RESULTS:
            
            **1. Exact Duplicate Detection:**
            {json.dumps(exact_results, indent=2, default=str)}
            
            **2. Semantic Duplicate Detection:**
            {json.dumps(semantic_results, indent=2, default=str)}
            
            **3. Business Key Duplicate Detection:**
            {json.dumps(business_results, indent=2, default=str)}
            
            **4. Deduplication Strategy Development:**
            {json.dumps(strategy_results, indent=2, default=str)}
            
            SYNTHESIS REQUIREMENTS:
            
            1. **CROSS-METHOD VALIDATION**:
               - Compare findings across different detection approaches
               - Identify overlapping duplicates found by multiple methods
               - Resolve conflicts between different detection results
               - Assess coverage gaps where duplicates might be missed
            
            2. **UNIFIED DUPLICATE ASSESSMENT**:
               - Provide single, authoritative duplicate status for the dataset
               - Consolidate duplicate counts and severity assessments
               - Determine overall UC4 status (DUPLICATES PRESENT vs CLEAN)
               - Calculate comprehensive data quality impact
            
            3. **INTEGRATED RESOLUTION STRATEGY**:
               - Consolidate recommendations from all detection agents
               - Prioritize resolution actions based on combined insights
               - Create unified implementation roadmap
               - Optimize resource allocation across different duplicate types
            
            4. **EXECUTIVE DECISION SUPPORT**:
               - Provide business-focused summary of duplicate findings
               - Assess cost-benefit of different resolution approaches
               - Give clear recommendations for immediate vs long-term actions
               - Quantify expected business value of duplicate resolution
            
            5. **STRATEGIC INSIGHTS AND GOVERNANCE**:
               - Identify root causes of duplicate creation
               - Recommend systematic improvements to prevent future duplicates
               - Provide data governance and process improvement recommendations
               - Establish ongoing monitoring and quality assurance framework
            
            EXPECTED OUTPUT FORMAT:
            ```json
            {{
                "uc4_overall_assessment": {{
                    "dataset_duplicate_status": "high_duplicates|moderate_duplicates|low_duplicates|clean",
                    "confidence_level": "high|medium|low",
                    "total_duplicates_all_methods": number,
                    "business_impact_severity": "critical|high|medium|low",
                    "immediate_action_required": "yes|no|conditional"
                }},
                "cross_method_validation": {{
                    "detection_method_agreement": "high|medium|low",
                    "overlapping_duplicates": number,
                    "method_specific_findings": ["unique insights from each method"],
                    "coverage_assessment": "comprehensive|good|gaps_identified"
                }},
                "unified_duplicate_summary": {{
                    "exact_duplicates": number,
                    "semantic_duplicates": number,
                    "business_key_duplicates": number,
                    "complex_cases": number,
                    "total_unique_duplicate_groups": number,
                    "estimated_deduplication_impact": "data quality improvement percentage"
                }},
                "prioritized_resolution_plan": {{
                    "immediate_priority": [
                        {{
                            "duplicate_type": "specific type",
                            "count": number,
                            "resolution_method": "automated|semi-automated|manual",
                            "business_justification": "why immediate priority",
                            "estimated_effort": "time/resource estimate"
                        }}
                    ],
                    "short_term": ["1-4 week actions"],
                    "medium_term": ["1-3 month strategic actions"],
                    "long_term": ["3+ month governance improvements"]
                }},
                "business_value_analysis": {{
                    "cost_of_duplicates": "estimated cost impact",
                    "resolution_investment_required": "estimated effort/cost",
                    "expected_roi": "return on investment estimate",
                    "qualitative_benefits": ["business process improvements"]
                }},
                "implementation_guidance": {{
                    "recommended_starting_point": "specific first action",
                    "success_criteria": ["measurable success indicators"],
                    "risk_mitigation": ["key risks and mitigation strategies"],
                    "resource_requirements": ["team and technology needs"]
                }},
                "prevention_and_governance": {{
                    "root_cause_analysis": ["primary causes of duplicate creation"],
                    "process_improvements": ["business process changes needed"],
                    "technology_solutions": ["technical prevention measures"],
                    "ongoing_monitoring": ["continuous quality assurance framework"]
                }}
            }}
            ```
            
            Provide authoritative synthesis that integrates all detection methods and gives clear strategic direction for duplicate resolution.
            """
            
            synthesis_response = self.agent.run(synthesis_prompt)
            
            # Step 3: Create unified results structure
            unified_results = BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                analysis_type="complete_uc4_analysis",
                similarity_threshold=similarity_threshold,
                
                # Individual agent results
                exact_duplicate_analysis=exact_results,
                semantic_duplicate_analysis=semantic_results,
                business_key_analysis=business_results,
                deduplication_strategy=strategy_results,
                
                # Synthesized insights
                orchestration_synthesis=synthesis_response.content if hasattr(synthesis_response, 'content') else str(synthesis_response),
                
                # Analysis metadata
                agents_executed=["ExactDuplicateDetectionAgent", "SemanticDuplicateAgent", "BusinessKeyDuplicateAgent", "DeduplicationStrategyAgent"],
                analysis_focus="Complete UC4 duplicate detection and resolution strategy"
            )
            
            log_agent_activity(self.agent_name, "Complete UC4 analysis finished", 
                             {"execution_time_ms": unified_results["execution_time_ms"],
                              "agents_count": 4})
            
            print("[UC4 Orchestrator] Analysis completed successfully")
            return unified_results
            
        except Exception as e:
            log_agent_activity(self.agent_name, "UC4 analysis failed", {"error": str(e)})
            return BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                success=False,
                error=str(e)
            )


# Export the main orchestration agent for use by the FastAPI backend
def get_uc4_agent() -> UC4OrchestrationAgent:
    """Get the main UC4 orchestration agent instance"""
    return UC4OrchestrationAgent()


# For backward compatibility, also export individual agents
def get_uc4_exact_duplicate_agent() -> ExactDuplicateDetectionAgent:
    """Get the exact duplicate detection agent"""
    return ExactDuplicateDetectionAgent()


def get_uc4_semantic_duplicate_agent() -> SemanticDuplicateAgent:
    """Get the semantic duplicate detection agent"""
    return SemanticDuplicateAgent()


def get_uc4_business_key_agent() -> BusinessKeyDuplicateAgent:
    """Get the business key duplicate detection agent"""
    return BusinessKeyDuplicateAgent()


def get_uc4_deduplication_strategy_agent() -> DeduplicationStrategyAgent:
    """Get the deduplication strategy agent"""
    return DeduplicationStrategyAgent()
