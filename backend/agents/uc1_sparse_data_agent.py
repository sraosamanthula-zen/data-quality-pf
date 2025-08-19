"""
UC1: Incomplete or Sparse Data Files Detection System

This module contains multiple specialized agents for detecting and analyzing sparse or incomplete data files.
Each agent focuses on a specific aspect of data completeness using Agno framework with Azure OpenAI.

Agents included:
1. DataCompletenessAgent - Overall completeness analysis
2. SparseColumnDetectionAgent - Column-level sparsity detection
3. EmptyRowAnalysisAgent - Row-level completeness analysis
4. DataQualityScoreAgent - Quality scoring and recommendations
5. UC1OrchestrationAgent - Coordinates all UC1 agents
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import os
from pathlib import Path

from agno.agent import Agent
from agno.tools.file import FileTools
from agno.tools.python import PythonTools
from agno.tools.reasoning import ReasoningTools
from .base_config import AgentConfig, BaseAgentResults, log_agent_activity


class DataCompletenessAgent:
    """
    Agent specialized in analyzing overall data completeness metrics.
    Uses Agno's FileTools and PythonTools for data analysis.
    """
    
    def __init__(self):
        self.agent_name = "UC1_DataCompletenessAgent"
        self.config = AgentConfig()
        
        # Create agent with Azure OpenAI and specialized tools
        self.agent = Agent(
            name="Data Completeness Analysis Agent",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                FileTools(),
                PythonTools(run_code=True, uv_pip_install=False,),
                ReasoningTools(add_instructions=True)
            ],
            instructions=[
                "You are a DATA COMPLETENESS EXPERT specialized in analyzing CSV files for missing data patterns.",
                "",
                "CORE RESPONSIBILITIES:",
                "- Calculate precise completeness percentages for entire datasets",
                "- Analyze missing data patterns across columns and rows", 
                "- Identify systematic vs random missing data",
                "- Provide statistical insights on data completeness",
                "",
                "ANALYSIS METHODOLOGY:",
                "1. Load and examine the CSV file structure",
                "2. Calculate total cells, missing cells, and completeness percentage",
                "3. Analyze missing data patterns (random, systematic, structural)",
                "4. Generate column-wise completeness statistics",
                "5. Identify correlations between missing data in different columns",
                "",
                "OUTPUT REQUIREMENTS:",
                "- Provide precise numerical completeness metrics",
                "- Categorize missing data patterns (MCAR, MAR, MNAR)",
                "- Highlight columns with concerning completeness levels",
                "- Recommend data collection improvements",
                "",
                "QUALITY STANDARDS:",
                "- 95%+ completeness: Excellent data quality",
                "- 85-94% completeness: Good data quality with minor gaps",
                "- 70-84% completeness: Fair data quality requiring attention", 
                "- <70% completeness: Poor data quality requiring intervention",
                "",
                "Always use the available tools to perform actual data analysis and provide concrete, actionable insights."
            ],
            add_datetime_to_instructions=True,
            markdown=True,
            debug_mode=True
        )
    
    async def analyze_completeness(self, file_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive data completeness analysis
        
        Args:
            file_path: Path to the CSV file to analyze
            
        Returns:
            Dictionary containing detailed completeness analysis
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting completeness analysis", {"file": file_path})
        
        try:
            # Create detailed analysis prompt
            analysis_prompt = f"""
            Please perform a comprehensive DATA COMPLETENESS ANALYSIS for the file: {file_path}

            REQUIRED ANALYSIS STEPS:
            
            1. **FILE EXAMINATION**:
               - Use file tools to read the CSV file
               - Examine file structure, columns, and data types
               - Calculate basic file metrics (rows, columns, total cells)
            
            2. **COMPLETENESS CALCULATIONS**:
               - Calculate overall completeness percentage
               - Generate per-column completeness statistics
               - Identify completely empty columns or rows
               - Calculate missing data density across the dataset
            
            3. **MISSING DATA PATTERN ANALYSIS**:
               - Determine if missing data is random (MCAR), at random (MAR), or not at random (MNAR)
               - Identify columns that frequently have missing data together
               - Detect systematic missing data patterns (e.g., entire sections, periodic gaps)
            
            4. **STATISTICAL INSIGHTS**:
               - Calculate variance in completeness across columns
               - Identify outlier columns (significantly more/less complete)
               - Analyze distribution of missing data across rows
            
            5. **BUSINESS IMPACT ASSESSMENT**:
               - Categorize each column by business criticality vs completeness
               - Identify high-impact missing data (key business fields)
               - Assess data reliability for downstream processing
            
            EXPECTED OUTPUT FORMAT:
            ```json
            {{
                "overall_completeness": {{
                    "total_cells": number,
                    "missing_cells": number,
                    "completeness_percentage": number,
                    "quality_category": "excellent|good|fair|poor"
                }},
                "column_analysis": {{
                    "column_name": {{
                        "missing_count": number,
                        "completeness_percentage": number,
                        "pattern_type": "random|systematic|structural",
                        "business_impact": "critical|high|medium|low"
                    }}
                }},
                "missing_patterns": {{
                    "pattern_type": "description",
                    "affected_columns": ["list"],
                    "correlation_analysis": "insights"
                }},
                "recommendations": [
                    "specific actionable recommendations"
                ]
            }}
            ```
            
            Use Python tools to perform actual calculations and file tools to read the data.
            Provide concrete numerical results, not estimates.
            """
            
            # Get agent analysis
            response = self.agent.run(analysis_prompt)
            
            # Structure results
            results = BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                analysis_type="data_completeness",
                agent_response=response.content if hasattr(response, 'content') else str(response),
                analysis_focus="Overall data completeness and missing data patterns"
            )
            
            log_agent_activity(self.agent_name, "Completeness analysis completed", 
                             {"execution_time_ms": results["execution_time_ms"]})
            
            return results
            
        except Exception as e:
            log_agent_activity(self.agent_name, "Analysis failed", {"error": str(e)})
            return BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                success=False,
                error=str(e)
            )


class SparseColumnDetectionAgent:
    """
    Agent specialized in detecting and analyzing sparse columns in datasets.
    Focuses on column-level sparsity patterns and business impact.
    """
    
    def __init__(self):
        self.agent_name = "UC1_SparseColumnDetectionAgent"
        self.config = AgentConfig()
        
        self.agent = Agent(
            name="Sparse Column Detection Specialist",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                FileTools(),
                PythonTools(run_code=True, uv_pip_install=False,),
                ReasoningTools(add_instructions=True)
            ],
            instructions=[
                "You are a SPARSE COLUMN DETECTION SPECIALIST with expertise in identifying problematic sparse columns in datasets.",
                "",
                "SPECIALIZED FOCUS:",
                "- Identify columns with high missing data ratios (>50% missing)",
                "- Classify sparse columns by severity and business impact",
                "- Analyze sparsity patterns within individual columns",
                "- Recommend column treatment strategies (imputation, removal, flagging)",
                "",
                "SPARSITY CLASSIFICATION FRAMEWORK:",
                "• CRITICAL SPARSITY (>80% missing): Requires immediate attention",
                "• HIGH SPARSITY (60-80% missing): Significant data quality concern", 
                "• MODERATE SPARSITY (40-60% missing): Moderate concern requiring monitoring",
                "• LOW SPARSITY (20-40% missing): Minor concern, may be acceptable",
                "",
                "ANALYSIS DIMENSIONS:",
                "1. Quantitative sparsity metrics (missing ratios, counts)",
                "2. Sparsity distribution patterns (clustered vs scattered)",
                "3. Column data type impact on sparsity interpretation",
                "4. Business criticality assessment for each sparse column",
                "5. Correlation between sparse columns",
                "",
                "TREATMENT RECOMMENDATIONS:",
                "- Imputation strategies for recoverable sparse columns",
                "- Removal recommendations for non-recoverable columns",
                "- Data collection improvements for future prevention",
                "- Alternative data sources for critical sparse columns",
                "",
                "Always provide actionable insights with clear business justification for each recommendation."
            ],
            add_datetime_to_instructions=True,
            markdown=True,
            debug_mode=True
        )
    
    async def detect_sparse_columns(self, file_path: str, sparsity_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Detect and analyze sparse columns in the dataset
        
        Args:
            file_path: Path to the CSV file to analyze
            sparsity_threshold: Threshold for considering a column sparse (default 0.5 = 50% missing)
            
        Returns:
            Dictionary containing sparse column analysis
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting sparse column detection", 
                         {"file": file_path, "threshold": sparsity_threshold})
        
        try:
            analysis_prompt = f"""
            Perform SPECIALIZED SPARSE COLUMN DETECTION AND ANALYSIS for file: {file_path}
            
            ANALYSIS PARAMETERS:
            - Sparsity threshold: {sparsity_threshold} ({sparsity_threshold*100}% missing data)
            - Focus: Column-level sparsity patterns and business impact
            
            REQUIRED ANALYSIS STEPS:
            
            1. **COLUMN SPARSITY SCANNING**:
               - Load CSV file and examine all columns
               - Calculate missing data ratio for each column
               - Identify columns exceeding the sparsity threshold
               - Rank columns by sparsity severity
            
            2. **SPARSITY PATTERN ANALYSIS**:
               - Analyze missing data distribution within each sparse column
               - Detect if missing values are clustered or randomly distributed
               - Identify potential causes of sparsity (data collection issues, optional fields, etc.)
            
            3. **BUSINESS IMPACT CLASSIFICATION**:
               - Categorize each sparse column by potential business importance
               - Assess impact on data analysis and decision-making
               - Identify columns that might be acceptable despite sparsity
            
            4. **COLUMN INTERDEPENDENCY ANALYSIS**:
               - Examine correlations between sparse columns
               - Identify groups of columns that tend to be missing together
               - Detect cascading sparsity effects
            
            5. **TREATMENT STRATEGY RECOMMENDATIONS**:
               For each sparse column, recommend specific treatment:
               - Imputation (mean, median, mode, forward-fill, etc.)
               - Removal (if non-critical and highly sparse)
               - Data collection improvement
               - Alternative data source integration
               - Accept as-is (if business-justified)
            
            EXPECTED OUTPUT FORMAT:
            ```json
            {{
                "sparse_columns_detected": number,
                "sparsity_threshold_used": {sparsity_threshold},
                "severity_breakdown": {{
                    "critical": number,
                    "high": number,
                    "moderate": number,
                    "low": number
                }},
                "detailed_analysis": {{
                    "column_name": {{
                        "missing_ratio": number,
                        "missing_count": number,
                        "severity_level": "critical|high|moderate|low",
                        "pattern_type": "clustered|random|systematic",
                        "business_impact": "critical|high|medium|low",
                        "recommended_treatment": "specific treatment strategy",
                        "treatment_justification": "detailed reasoning"
                    }}
                }},
                "correlation_analysis": {{
                    "correlated_sparse_groups": ["group descriptions"],
                    "independent_sparse_columns": ["column names"]
                }},
                "priority_actions": [
                    "ordered list of highest priority remediation actions"
                ]
            }}
            ```
            
            Use Python and file tools to perform actual analysis. Provide specific, actionable recommendations.
            """
            
            response = self.agent.run(analysis_prompt)
            
            results = BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                analysis_type="sparse_column_detection",
                sparsity_threshold=sparsity_threshold,
                agent_response=response.content if hasattr(response, 'content') else str(response),
                analysis_focus="Column-level sparsity detection and treatment recommendations"
            )
            
            log_agent_activity(self.agent_name, "Sparse column detection completed", 
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


class EmptyRowAnalysisAgent:
    """
    Agent specialized in detecting and analyzing empty or nearly empty rows.
    Focuses on row-level completeness and data integrity.
    """
    
    def __init__(self):
        self.agent_name = "UC1_EmptyRowAnalysisAgent"
        self.config = AgentConfig()
        
        self.agent = Agent(
            name="Empty Row Analysis Specialist",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                FileTools(),
                PythonTools(run_code=True, uv_pip_install=False,),
                ReasoningTools(add_instructions=True)
            ],
            instructions=[
                "You are an EMPTY ROW ANALYSIS SPECIALIST focused on detecting and analyzing problematic rows in datasets.",
                "",
                "SPECIALIZED EXPERTISE:",
                "- Detect completely empty rows (all fields null/blank)",
                "- Identify nearly empty rows (minimal data present)",
                "- Analyze row-level data completeness patterns",
                "- Assess impact of empty rows on data processing",
                "",
                "ROW COMPLETENESS CATEGORIES:",
                "• COMPLETELY EMPTY: All fields are null, blank, or whitespace",
                "• MOSTLY EMPTY (>90% missing): Only 1-2 fields contain data",
                "• SUBSTANTIALLY EMPTY (70-90% missing): Significant data gaps",
                "• PARTIALLY EMPTY (40-70% missing): Some useful data present",
                "",
                "ANALYSIS FOCUS AREAS:",
                "1. Empty row detection and quantification",
                "2. Row completeness distribution analysis",
                "3. Pattern identification (consecutive empty rows, periodic gaps)",
                "4. Impact assessment on data integrity and processing",
                "5. Recommendations for row handling strategies",
                "",
                "ROW TREATMENT STRATEGIES:",
                "- Removal of completely empty rows",
                "- Conditional removal based on business rules",
                "- Flagging for manual review",
                "- Imputation at row level where appropriate",
                "",
                "QUALITY IMPACT ASSESSMENT:",
                "- Effect on statistical calculations",
                "- Impact on data joins and relationships", 
                "- Influence on machine learning model training",
                "- Business process implications",
                "",
                "Always provide specific row indices and clear remediation strategies."
            ],
            add_datetime_to_instructions=True,
            markdown=True,
            debug_mode=True
        )
    
    async def analyze_empty_rows(self, file_path: str, empty_threshold: float = 0.9) -> Dict[str, Any]:
        """
        Analyze empty and nearly empty rows in the dataset
        
        Args:
            file_path: Path to the CSV file to analyze
            empty_threshold: Threshold for considering a row "mostly empty" (default 0.9 = 90% missing)
            
        Returns:
            Dictionary containing empty row analysis
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting empty row analysis", 
                         {"file": file_path, "empty_threshold": empty_threshold})
        
        try:
            analysis_prompt = f"""
            Perform COMPREHENSIVE EMPTY ROW ANALYSIS for file: {file_path}
            
            ANALYSIS PARAMETERS:
            - Empty row threshold: {empty_threshold} ({empty_threshold*100}% missing data in a row)
            - Focus: Row-level completeness and data integrity
            
            REQUIRED ANALYSIS STEPS:
            
            1. **ROW COMPLETENESS SCANNING**:
               - Load CSV file and examine row-by-row completeness
               - Identify completely empty rows (all fields null/blank)
               - Find mostly empty rows exceeding the threshold
               - Calculate row completeness distribution
            
            2. **EMPTY ROW PATTERN ANALYSIS**:
               - Detect consecutive empty rows (potential data gaps)
               - Identify periodic empty row patterns
               - Analyze empty row distribution across the dataset
               - Determine if empty rows correlate with specific data sections
            
            3. **ROW QUALITY CATEGORIZATION**:
               - Classify each problematic row by emptiness severity
               - Identify rows with minimal but potentially useful data
               - Assess which rows are candidates for different treatments
            
            4. **DATA INTEGRITY IMPACT ASSESSMENT**:
               - Evaluate how empty rows affect data analysis
               - Assess impact on statistical calculations
               - Determine effects on data relationships and joins
               - Analyze influence on downstream processing
            
            5. **ROW TREATMENT RECOMMENDATIONS**:
               - Immediate removal candidates (completely empty)
               - Conditional removal candidates (mostly empty, non-critical)
               - Manual review candidates (partially empty, potentially recoverable)
               - Imputation candidates (strategic missing data)
            
            EXPECTED OUTPUT FORMAT:
            ```json
            {{
                "row_analysis_summary": {{
                    "total_rows": number,
                    "completely_empty_rows": number,
                    "mostly_empty_rows": number,
                    "problematic_rows_percentage": number
                }},
                "empty_row_patterns": {{
                    "consecutive_empty_sections": [
                        {{
                            "start_row": number,
                            "end_row": number,
                            "length": number,
                            "pattern_type": "description"
                        }}
                    ],
                    "periodic_patterns": "description of any periodic empty row patterns",
                    "random_distribution": "assessment of random vs systematic empty rows"
                }},
                "row_completeness_distribution": {{
                    "completely_empty": number,
                    "mostly_empty_90_plus": number,
                    "substantially_empty_70_90": number,
                    "partially_empty_40_70": number,
                    "acceptable_completeness": number
                }},
                "problematic_rows_details": {{
                    "row_index": {{
                        "completeness_percentage": number,
                        "empty_fields_count": number,
                        "severity": "critical|high|medium|low",
                        "recommended_action": "remove|review|impute|accept",
                        "justification": "reasoning for recommendation"
                    }}
                }},
                "impact_assessment": {{
                    "data_integrity_risk": "high|medium|low",
                    "processing_complications": ["list of potential issues"],
                    "business_impact": "assessment of business implications"
                }},
                "remediation_plan": [
                    "step-by-step plan for handling empty rows"
                ]
            }}
            ```
            
            Use Python and file tools for actual row-by-row analysis. Provide specific row indices for first 10-20 problematic rows as examples.
            """
            
            response = self.agent.run(analysis_prompt)
            
            results = BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                analysis_type="empty_row_analysis",
                empty_threshold=empty_threshold,
                agent_response=response.content if hasattr(response, 'content') else str(response),
                analysis_focus="Row-level completeness and empty row detection"
            )
            
            log_agent_activity(self.agent_name, "Empty row analysis completed", 
                             {"execution_time_ms": results["execution_time_ms"]})
            
            return results
            
        except Exception as e:
            log_agent_activity(self.agent_name, "Analysis failed", {"error": str(e)})
            return BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                success=False,
                error=str(e)
            )


class DataQualityScoreAgent:
    """
    Agent specialized in calculating comprehensive data quality scores and providing recommendations.
    Synthesizes insights from other UC1 agents into actionable quality metrics.
    """
    
    def __init__(self):
        self.agent_name = "UC1_DataQualityScoreAgent"
        self.config = AgentConfig()
        
        self.agent = Agent(
            name="Data Quality Scoring Expert",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                FileTools(),
                PythonTools(run_code=True, uv_pip_install=False,),
                ReasoningTools(add_instructions=True)
            ],
            instructions=[
                "You are a DATA QUALITY SCORING EXPERT responsible for calculating comprehensive quality scores and providing strategic recommendations.",
                "",
                "CORE RESPONSIBILITIES:",
                "- Calculate weighted data quality scores (0-100 scale)",
                "- Synthesize multiple quality dimensions into overall assessment",
                "- Provide strategic recommendations for data quality improvement",
                "- Generate executive-level quality reports",
                "",
                "QUALITY SCORING FRAMEWORK:",
                "• COMPLETENESS SCORE (40% weight): Overall data completeness",
                "• SPARSITY IMPACT SCORE (30% weight): Impact of sparse columns",
                "• ROW INTEGRITY SCORE (20% weight): Row-level completeness",
                "• PATTERN CONSISTENCY SCORE (10% weight): Data pattern reliability",
                "",
                "SCORING SCALE:",
                "• 90-100: EXCELLENT - Production ready, minimal intervention needed",
                "• 75-89: GOOD - Minor improvements recommended",
                "• 60-74: FAIR - Moderate improvements required",
                "• 40-59: POOR - Significant improvements needed",
                "• 0-39: CRITICAL - Major intervention required before use",
                "",
                "RECOMMENDATION CATEGORIES:",
                "1. IMMEDIATE ACTIONS: Critical issues requiring immediate attention",
                "2. SHORT-TERM IMPROVEMENTS: Issues to address within 1-2 weeks",
                "3. LONG-TERM ENHANCEMENTS: Strategic improvements over 1-3 months",
                "4. MONITORING SETUP: Ongoing quality monitoring recommendations",
                "",
                "BUSINESS IMPACT ASSESSMENT:",
                "- Risk assessment for using data in current state",
                "- Cost-benefit analysis of quality improvements",
                "- Prioritization based on business criticality",
                "- ROI estimates for recommended improvements",
                "",
                "Always provide specific, measurable recommendations with clear business justification."
            ],
            add_datetime_to_instructions=True,
            markdown=True,
            debug_mode=True
        )
    
    async def calculate_quality_score(self, file_path: str, 
                                    completeness_analysis: Dict = None,
                                    sparse_analysis: Dict = None,
                                    empty_row_analysis: Dict = None) -> Dict[str, Any]:
        """
        Calculate comprehensive data quality score and recommendations
        
        Args:
            file_path: Path to the CSV file to analyze
            completeness_analysis: Results from DataCompletenessAgent (optional)
            sparse_analysis: Results from SparseColumnDetectionAgent (optional)
            empty_row_analysis: Results from EmptyRowAnalysisAgent (optional)
            
        Returns:
            Dictionary containing quality score and comprehensive recommendations
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting quality score calculation", {"file": file_path})
        
        try:
            # Prepare analysis context
            analysis_context = {
                "completeness_analysis": completeness_analysis or {},
                "sparse_analysis": sparse_analysis or {},
                "empty_row_analysis": empty_row_analysis or {}
            }
            
            analysis_prompt = f"""
            Calculate COMPREHENSIVE DATA QUALITY SCORE AND RECOMMENDATIONS for file: {file_path}
            
            AVAILABLE ANALYSIS RESULTS:
            {json.dumps(analysis_context, indent=2, default=str)}
            
            SCORING METHODOLOGY:
            
            1. **COMPLETENESS SCORE CALCULATION (40% weight)**:
               - Base score from overall data completeness percentage
               - Adjust for critical vs non-critical missing fields
               - Factor in missing data patterns (random vs systematic)
               
            2. **SPARSITY IMPACT SCORE (30% weight)**:
               - Penalize based on number and severity of sparse columns
               - Weight by business criticality of sparse fields
               - Consider treatment feasibility for sparse columns
               
            3. **ROW INTEGRITY SCORE (20% weight)**:
               - Penalize for empty and mostly empty rows
               - Factor in row pattern consistency
               - Assess impact on data relationships
               
            4. **PATTERN CONSISTENCY SCORE (10% weight)**:
               - Evaluate data pattern reliability
               - Assess structural consistency
               - Factor in data collection quality indicators
            
            If analysis results are not provided, perform fresh analysis using available tools.
            
            REQUIRED OUTPUT SECTIONS:
            
            1. **QUALITY SCORE BREAKDOWN**:
               ```json
               {{
                   "overall_quality_score": number,
                   "score_category": "excellent|good|fair|poor|critical",
                   "component_scores": {{
                       "completeness_score": number,
                       "sparsity_impact_score": number,
                       "row_integrity_score": number,
                       "pattern_consistency_score": number
                   }},
                   "scoring_weights": {{
                       "completeness": 40,
                       "sparsity_impact": 30,
                       "row_integrity": 20,
                       "pattern_consistency": 10
                   }}
               }}
               ```
            
            2. **DETAILED ASSESSMENT**:
               - Strengths: What aspects of data quality are good
               - Weaknesses: Major quality concerns identified
               - Risk factors: Potential issues for downstream processing
               - Business impact: How quality issues affect business operations
            
            3. **STRATEGIC RECOMMENDATIONS**:
               ```json
               {{
                   "immediate_actions": [
                       {{
                           "action": "specific action",
                           "priority": "critical|high|medium",
                           "estimated_effort": "time estimate",
                           "expected_impact": "improvement description"
                       }}
                   ],
                   "short_term_improvements": [
                       "1-2 week recommendations"
                   ],
                   "long_term_enhancements": [
                       "1-3 month strategic improvements"
                   ],
                   "monitoring_setup": [
                       "ongoing quality monitoring recommendations"
                   ]
               }}
               ```
            
            4. **BUSINESS DECISION SUPPORT**:
               - Is data suitable for current intended use?
               - What are the risks of proceeding without improvements?
               - What is the estimated ROI of recommended improvements?
               - Which improvements should be prioritized first?
            
            5. **QUALITY IMPROVEMENT ROADMAP**:
               - Phase 1: Critical fixes (immediate)
               - Phase 2: Core improvements (1-4 weeks)
               - Phase 3: Enhancements (1-3 months)
               - Phase 4: Excellence initiatives (3+ months)
            
            Use all available tools to perform comprehensive analysis and provide specific, actionable recommendations.
            """
            
            response = self.agent.run(analysis_prompt)
            
            results = BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                analysis_type="quality_score_calculation",
                input_analyses=analysis_context,
                agent_response=response.content if hasattr(response, 'content') else str(response),
                analysis_focus="Comprehensive quality scoring and strategic recommendations"
            )
            
            log_agent_activity(self.agent_name, "Quality score calculation completed", 
                             {"execution_time_ms": results["execution_time_ms"]})
            
            return results
            
        except Exception as e:
            log_agent_activity(self.agent_name, "Scoring failed", {"error": str(e)})
            return BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                success=False,
                error=str(e)
            )


class UC1OrchestrationAgent:
    """
    Orchestration agent that coordinates all UC1 specialized agents and provides unified results.
    This agent manages the workflow and synthesizes insights from all other UC1 agents.
    """
    
    def __init__(self):
        self.agent_name = "UC1_OrchestrationAgent"
        self.config = AgentConfig()
        
        # Initialize all specialized agents
        self.completeness_agent = DataCompletenessAgent()
        self.sparse_column_agent = SparseColumnDetectionAgent()
        self.empty_row_agent = EmptyRowAnalysisAgent()
        self.quality_score_agent = DataQualityScoreAgent()
        
        self.agent = Agent(
            name="UC1 Sparse Data Detection Orchestrator",
            model=self.config.get_azure_openai_model(temperature=0.1),
            tools=[
                ReasoningTools(add_instructions=True)
            ],
            instructions=[
                "You are the UC1 ORCHESTRATION AGENT responsible for coordinating comprehensive sparse data detection and analysis.",
                "",
                "ORCHESTRATION RESPONSIBILITIES:",
                "- Coordinate execution of all specialized UC1 agents",
                "- Synthesize results from multiple agents into unified insights",
                "- Resolve conflicts or inconsistencies between agent findings",
                "- Provide executive summary of complete UC1 analysis",
                "",
                "AGENT COORDINATION WORKFLOW:",
                "1. DataCompletenessAgent: Overall completeness analysis",
                "2. SparseColumnDetectionAgent: Column-level sparsity detection",
                "3. EmptyRowAnalysisAgent: Row-level completeness analysis",
                "4. DataQualityScoreAgent: Comprehensive scoring and recommendations",
                "5. Synthesis: Unified insights and strategic guidance",
                "",
                "SYNTHESIS CAPABILITIES:",
                "- Cross-validate findings between agents",
                "- Identify patterns that emerge across multiple analyses", 
                "- Resolve inconsistencies in agent recommendations",
                "- Prioritize actions based on combined insights",
                "- Generate executive-level summary reports",
                "",
                "OUTPUT INTEGRATION:",
                "- Unified data quality assessment",
                "- Consolidated recommendations with clear prioritization",
                "- Cross-agent insights and pattern recognition",
                "- Strategic roadmap for data quality improvement",
                "",
                "Always ensure all agent findings are properly integrated and any conflicts are resolved with clear reasoning."
            ],
            add_datetime_to_instructions=True,
            markdown=True,
            debug_mode=True
        )
    
    async def analyze_file_with_reference(self, file_path: str, reference_file_path: str = None) -> Dict[str, Any]:
        """
        Analyze file sparsity with optional reference file comparison
        
        Args:
            file_path: Path to the file to analyze
            reference_file_path: Optional path to reference file for comparison
            
        Returns:
            Dictionary containing analysis results with reference comparison
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting reference comparison analysis", 
                         {"file": file_path, "reference": reference_file_path})
        
        try:
            if reference_file_path:
                # Perform comparative analysis against reference
                comparison_prompt = f"""
                Perform COMPARATIVE SPARSE DATA ANALYSIS:
                
                Target file: {file_path}
                Reference file: {reference_file_path}
                
                COMPARISON REQUIREMENTS:
                
                1. **STRUCTURAL COMPARISON**:
                   - Compare column structures between files
                   - Identify missing or extra columns in target vs reference
                   - Assess data type consistency
                
                2. **COMPLETENESS COMPARISON**:
                   - Compare overall completeness percentages
                   - Calculate relative sparsity (target vs reference)
                   - Identify columns that are more sparse in target
                
                3. **PATTERN COMPARISON**:
                   - Compare missing data patterns
                   - Identify if target has systematic gaps not in reference
                   - Assess quality degradation from reference baseline
                
                4. **SPARSITY VERDICT**:
                   - Determine if target is "sparse compared to reference"
                   - Calculate sparsity score relative to reference (0-100)
                   - Provide clear recommendation
                
                Expected output should include:
                - sparse_compared_to_reference: boolean
                - sparsity_score: 0-100 (higher = more sparse than reference)
                - reference_comparison_details: detailed analysis
                """
                
                response = self.agent.run(comparison_prompt)
                
                # Also run standard analysis
                standard_results = await self.run_complete_uc1_analysis(file_path)
                
                # Combine results
                results = {
                    **standard_results,
                    "reference_comparison": response.content if hasattr(response, 'content') else str(response),
                    "reference_file_path": reference_file_path,
                    "has_reference": True
                }
                
            else:
                # Standard analysis without reference
                results = await self.run_complete_uc1_analysis(file_path)
                results["has_reference"] = False
            
            log_agent_activity(self.agent_name, "Reference comparison analysis completed", 
                             {"execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000})
            
            return results
            
        except Exception as e:
            log_agent_activity(self.agent_name, "Reference comparison failed", {"error": str(e)})
            return BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                success=False,
                error=str(e)
            )


    async def run_complete_uc1_analysis(self, file_path: str, 
                                      sparsity_threshold: float = 0.5,
                                      empty_threshold: float = 0.9) -> Dict[str, Any]:
        """
        Run complete UC1 sparse data detection analysis using all specialized agents
        
        Args:
            file_path: Path to the CSV file to analyze
            sparsity_threshold: Threshold for sparse column detection
            empty_threshold: Threshold for empty row detection
            
        Returns:
            Dictionary containing unified UC1 analysis results
        """
        start_time = datetime.now()
        log_agent_activity(self.agent_name, "Starting complete UC1 analysis", 
                         {"file": file_path, "sparsity_threshold": sparsity_threshold, "empty_threshold": empty_threshold})
        
        try:
            # Step 1: Run all specialized agents
            print(f"[UC1 Orchestrator] Running specialized agents for: {file_path}")
            
            # Execute agents in logical order
            completeness_results = await self.completeness_agent.analyze_completeness(file_path)
            sparse_results = await self.sparse_column_agent.detect_sparse_columns(file_path, sparsity_threshold)
            empty_row_results = await self.empty_row_agent.analyze_empty_rows(file_path, empty_threshold)
            quality_score_results = await self.quality_score_agent.calculate_quality_score(
                file_path, completeness_results, sparse_results, empty_row_results
            )
            
            # Step 2: Synthesize results using orchestration agent
            synthesis_prompt = f"""
            SYNTHESIZE COMPLETE UC1 SPARSE DATA DETECTION ANALYSIS
            
            File analyzed: {file_path}
            Analysis timestamp: {start_time.isoformat()}
            
            SPECIALIZED AGENT RESULTS:
            
            **1. Data Completeness Analysis:**
            {json.dumps(completeness_results, indent=2, default=str)}
            
            **2. Sparse Column Detection:**
            {json.dumps(sparse_results, indent=2, default=str)}
            
            **3. Empty Row Analysis:**
            {json.dumps(empty_row_results, indent=2, default=str)}
            
            **4. Quality Score Calculation:**
            {json.dumps(quality_score_results, indent=2, default=str)}
            
            SYNTHESIS REQUIREMENTS:
            
            1. **CROSS-VALIDATION**: 
               - Verify consistency between agent findings
               - Identify any conflicting insights and resolve them
               - Highlight patterns that emerge across multiple analyses
            
            2. **UNIFIED ASSESSMENT**:
               - Provide single, authoritative data quality judgment
               - Synthesize sparse data findings into clear conclusion
               - Determine overall UC1 status (SPARSE vs ACCEPTABLE)
            
            3. **INTEGRATED RECOMMENDATIONS**:
               - Consolidate recommendations from all agents
               - Prioritize actions based on combined insights
               - Remove redundant or conflicting recommendations
               - Create clear implementation roadmap
            
            4. **EXECUTIVE SUMMARY**:
               - Provide business-focused summary of findings
               - Highlight key risks and opportunities
               - Give clear go/no-go recommendation for data usage
            
            5. **STRATEGIC INSIGHTS**:
               - Identify root causes of sparse data issues
               - Recommend systematic improvements to prevent future sparsity
               - Provide data governance recommendations
            
            EXPECTED OUTPUT FORMAT:
            ```json
            {{
                "uc1_overall_assessment": {{
                    "file_classification": "sparse|acceptable|excellent",
                    "confidence_level": "high|medium|low",
                    "key_findings": ["top 3-5 findings"],
                    "critical_issues": ["issues requiring immediate attention"]
                }},
                "cross_agent_validation": {{
                    "consistency_check": "all agents aligned|minor discrepancies|major conflicts",
                    "resolved_conflicts": ["any conflicts found and how resolved"],
                    "emerging_patterns": ["patterns identified across multiple analyses"]
                }},
                "unified_recommendations": {{
                    "immediate_priority": ["actions needed within 24-48 hours"],
                    "short_term": ["actions needed within 1-2 weeks"],
                    "medium_term": ["actions needed within 1-3 months"],
                    "long_term": ["strategic improvements over 3+ months"]
                }},
                "business_decision_support": {{
                    "use_data_as_is": "yes|no|conditional",
                    "conditions_for_use": ["if conditional, what conditions"],
                    "risk_assessment": "low|medium|high|critical",
                    "business_impact": "assessment of impact on operations"
                }},
                "implementation_roadmap": [
                    "step-by-step implementation plan"
                ]
            }}
            ```
            
            Provide authoritative synthesis that resolves any agent conflicts and gives clear strategic direction.
            """
            
            synthesis_response = self.agent.run(synthesis_prompt)
            
            # Step 3: Create unified results structure
            unified_results = BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                analysis_type="complete_uc1_analysis",
                sparsity_threshold=sparsity_threshold,
                empty_threshold=empty_threshold,
                
                # Individual agent results
                completeness_analysis=completeness_results,
                sparse_column_analysis=sparse_results,
                empty_row_analysis=empty_row_results,
                quality_score_analysis=quality_score_results,
                
                # Synthesized insights
                orchestration_synthesis=synthesis_response.content if hasattr(synthesis_response, 'content') else str(synthesis_response),
                
                # Analysis metadata
                agents_executed=["DataCompletenessAgent", "SparseColumnDetectionAgent", "EmptyRowAnalysisAgent", "DataQualityScoreAgent"],
                analysis_focus="Complete UC1 sparse data detection and analysis"
            )
            
            log_agent_activity(self.agent_name, "Complete UC1 analysis finished", 
                             {"execution_time_ms": unified_results["execution_time_ms"],
                              "agents_count": 4})
            
            print(f"[UC1 Orchestrator] Analysis completed successfully")
            return unified_results
            
        except Exception as e:
            log_agent_activity(self.agent_name, "UC1 analysis failed", {"error": str(e)})
            return BaseAgentResults.create_result(
                agent_name=self.agent_name,
                file_path=file_path,
                start_time=start_time,
                success=False,
                error=str(e)
            )


# Export the main orchestration agent for use by the FastAPI backend
def get_uc1_agent() -> UC1OrchestrationAgent:
    """Get the main UC1 orchestration agent instance"""
    return UC1OrchestrationAgent()


# For backward compatibility, also export individual agents
def get_uc1_completeness_agent() -> DataCompletenessAgent:
    """Get the data completeness analysis agent"""
    return DataCompletenessAgent()


def get_uc1_sparse_column_agent() -> SparseColumnDetectionAgent:
    """Get the sparse column detection agent"""
    return SparseColumnDetectionAgent()


def get_uc1_empty_row_agent() -> EmptyRowAnalysisAgent:
    """Get the empty row analysis agent"""
    return EmptyRowAnalysisAgent()


def get_uc1_quality_score_agent() -> DataQualityScoreAgent:
    """Get the data quality scoring agent"""
    return DataQualityScoreAgent()
