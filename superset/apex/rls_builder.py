# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Dynamic RLS builder for Apex integration."""

import logging
from typing import Any, Dict, List, Optional, Set
from sqlalchemy import text
from sqlalchemy.sql import ClauseElement
from flask import current_app

from .hierarchy_registry import HierarchyRegistry, get_hierarchy_registry
from .entitlement_client import UserEntitlements, entitlement_client

logger = logging.getLogger(__name__)


class DynamicHierarchicalRLSBuilder:
    """
    Dynamic hierarchical RLS builder that supports any hierarchy type.
    
    Builds SQL filters based on user entitlements and hierarchy configurations.
    """
    
    def __init__(self, hierarchy_registry: HierarchyRegistry = None):
        self.hierarchy_registry = hierarchy_registry or get_hierarchy_registry()
    
    def build_filter(self, user_entitlements: UserEntitlements, dataset_schema: Any) -> Optional[str]:
        """
        Build SQL filters for all hierarchies based on user entitlements.
        
        Args:
            user_entitlements: User entitlements data
            dataset_schema: Dataset schema information
            
        Returns:
            Combined SQL filter string or None if no filters
        """
        try:
            filters = []
            
            for hierarchy_name, hierarchy_data in user_entitlements.row_level_filters.items():
                hierarchy_config = self.hierarchy_registry.get_hierarchy(hierarchy_name)
                if hierarchy_config and hierarchy_config.active:
                    filter_conditions = self._build_dynamic_filters(
                        hierarchy_config, 
                        hierarchy_data, 
                        dataset_schema
                    )
                    if filter_conditions:
                        filters.extend(filter_conditions)
            
            return self._combine_filters(filters)
            
        except Exception as e:
            logger.error(f"Failed to build RLS filters: {e}")
            return None
    
    def _build_dynamic_filters(self, hierarchy_config, user_access_data: Dict[str, Any], 
                             schema: Any) -> List[str]:
        """
        Build filters for any hierarchy type based on configuration.
        
        Args:
            hierarchy_config: Hierarchy configuration
            user_access_data: User access data for this hierarchy
            schema: Dataset schema
            
        Returns:
            List of SQL filter conditions
        """
        try:
            filters = []
            hierarchy_levels = hierarchy_config.hierarchy_definition
            column_mappings = hierarchy_config.column_mappings
            user_access = user_access_data.get('user_access', {})
            
            # Build inheritance map for hierarchical access
            inherited_access = self._build_inheritance_map(
                hierarchy_levels, 
                user_access, 
                hierarchy_config.inheritance_rules
            )
            
            # Generate SQL filters for each level
            for level in hierarchy_levels:
                if level in inherited_access and inherited_access[level]:
                    column_name = column_mappings.get(level, level)
                    if self._column_exists_in_schema(column_name, schema):
                        filter_condition = self._create_in_filter(
                            column_name, 
                            inherited_access[level]
                        )
                        if filter_condition:
                            filters.append(filter_condition)
            
            return filters
            
        except Exception as e:
            logger.error(f"Failed to build dynamic filters: {e}")
            return []
    
    def _build_inheritance_map(self, hierarchy_levels: List[str], user_access: Dict[str, List[str]], 
                             inheritance_rules: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Build access inheritance based on hierarchy levels.
        
        Args:
            hierarchy_levels: List of hierarchy levels
            user_access: User access data
            inheritance_rules: Inheritance configuration
            
        Returns:
            Dictionary mapping levels to accessible values
        """
        inherited_access = {}
        
        if not inheritance_rules.get('enabled', True):
            return user_access
        
        direction = inheritance_rules.get('direction', 'top_down')
        
        if direction == 'top_down':
            # Higher level access grants access to all lower levels
            for i, level in enumerate(hierarchy_levels):
                inherited_access[level] = set(user_access.get(level, []))
                
                # Inherit from higher levels
                for j in range(i):
                    parent_level = hierarchy_levels[j]
                    if user_access.get(parent_level):
                        # If user has access to parent level, 
                        # fetch all child values for current level
                        child_values = self._get_child_values(
                            parent_level, 
                            user_access[parent_level], 
                            level
                        )
                        inherited_access[level].update(child_values)
        
        elif direction == 'bottom_up':
            # Lower level access grants access to parent levels
            for i in range(len(hierarchy_levels) - 1, -1, -1):
                level = hierarchy_levels[i]
                inherited_access[level] = set(user_access.get(level, []))
                
                # Inherit to higher levels
                for j in range(i + 1, len(hierarchy_levels)):
                    child_level = hierarchy_levels[j]
                    if user_access.get(child_level):
                        # If user has access to child level,
                        # fetch all parent values for current level
                        parent_values = self._get_parent_values(
                            child_level,
                            user_access[child_level],
                            level
                        )
                        inherited_access[level].update(parent_values)
        
        # Convert sets back to lists
        return {k: list(v) for k, v in inherited_access.items()}
    
    def _get_child_values(self, parent_level: str, parent_values: List[str], child_level: str) -> Set[str]:
        """
        Fetch child values from hierarchy lookup service.
        
        Args:
            parent_level: Parent level name
            parent_values: List of parent values
            child_level: Child level name
            
        Returns:
            Set of child values
        """
        try:
            # This would typically query a hierarchy lookup table/service
            # For now, we'll use the entitlement client to fetch hierarchy data
            hierarchy_name = None  # We would need to pass this or derive it
            
            if hierarchy_name:
                children = entitlement_client.get_hierarchy_children(
                    hierarchy_name, parent_level, parent_values, child_level
                )
                return set(children)
            
            return set()
            
        except Exception as e:
            logger.error(f"Failed to get child values: {e}")
            return set()
    
    def _get_parent_values(self, child_level: str, child_values: List[str], parent_level: str) -> Set[str]:
        """
        Fetch parent values from hierarchy lookup service.
        
        Args:
            child_level: Child level name
            child_values: List of child values
            parent_level: Parent level name
            
        Returns:
            Set of parent values
        """
        try:
            # This would typically query a hierarchy lookup table/service
            # Implementation would depend on the service API design
            return set()
            
        except Exception as e:
            logger.error(f"Failed to get parent values: {e}")
            return set()
    
    def _column_exists_in_schema(self, column_name: str, schema: Any) -> bool:
        """
        Check if column exists in dataset schema.
        
        Args:
            column_name: Column name to check
            schema: Dataset schema
            
        Returns:
            True if column exists, False otherwise
        """
        try:
            if hasattr(schema, 'columns'):
                return column_name in [col.name for col in schema.columns]
            elif hasattr(schema, 'get_column_names'):
                return column_name in schema.get_column_names()
            elif isinstance(schema, dict):
                return column_name in schema.get('columns', [])
            else:
                # Fallback: assume column exists
                logger.warning(f"Cannot determine schema type, assuming column {column_name} exists")
                return True
                
        except Exception as e:
            logger.error(f"Error checking column existence: {e}")
            return False
    
    def _create_in_filter(self, column_name: str, values: List[str]) -> Optional[str]:
        """
        Create SQL IN filter condition.
        
        Args:
            column_name: Column name
            values: List of values
            
        Returns:
            SQL filter string or None
        """
        if not values:
            return None
        
        try:
            # Escape single quotes in values
            escaped_values = [value.replace("'", "''") if isinstance(value, str) else str(value) for value in values]
            
            # Create IN clause
            values_str = ', '.join(f"'{value}'" for value in escaped_values)
            return f"{column_name} IN ({values_str})"
            
        except Exception as e:
            logger.error(f"Error creating IN filter: {e}")
            return None
    
    def _combine_filters(self, filters: List[str]) -> Optional[str]:
        """
        Combine multiple filters with AND logic.
        
        Args:
            filters: List of filter conditions
            
        Returns:
            Combined filter string or None
        """
        valid_filters = [f for f in filters if f is not None and f.strip()]
        
        if not valid_filters:
            return None
        
        if len(valid_filters) == 1:
            return valid_filters[0]
        
        return " AND ".join(f"({f})" for f in valid_filters)


class RLSQueryBuilder:
    """
    Query builder that applies RLS filters to SQL queries.
    """
    
    def __init__(self, hierarchy_registry: HierarchyRegistry = None):
        self.hierarchy_registry = hierarchy_registry or get_hierarchy_registry()
        self.rls_builder = DynamicHierarchicalRLSBuilder(hierarchy_registry)
    
    def apply_rls_filters(self, query: Any, user_entitlements: UserEntitlements, dataset: Any) -> Any:
        """
        Apply RLS filters to a query.
        
        Args:
            query: SQL query object
            user_entitlements: User entitlements
            dataset: Dataset object
            
        Returns:
            Modified query with RLS filters applied
        """
        try:
            filters = self.rls_builder.build_filter(user_entitlements, dataset.schema if hasattr(dataset, 'schema') else dataset)
            
            if filters:
                # Apply filters to the query
                if hasattr(query, 'where'):
                    # SQLAlchemy query
                    query = query.where(text(filters))
                elif isinstance(query, str):
                    # Raw SQL string
                    if 'WHERE' in query.upper():
                        # Add to existing WHERE clause
                        query = query.replace(' WHERE ', f' WHERE ({filters}) AND ')
                    else:
                        # Add new WHERE clause
                        query = f"{query} WHERE {filters}"
                else:
                    logger.warning(f"Unknown query type: {type(query)}")
            
            return query
            
        except Exception as e:
            logger.error(f"Failed to apply RLS filters: {e}")
            return query
    
    def build_rls_clause(self, user_entitlements: UserEntitlements, dataset: Any) -> Optional[ClauseElement]:
        """
        Build RLS clause as SQLAlchemy clause element.
        
        Args:
            user_entitlements: User entitlements
            dataset: Dataset object
            
        Returns:
            SQLAlchemy clause element or None
        """
        try:
            filters = self.rls_builder.build_filter(user_entitlements, dataset.schema if hasattr(dataset, 'schema') else dataset)
            
            if filters:
                return text(filters)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to build RLS clause: {e}")
            return None


# Helper functions for integration with Superset

def get_rls_filter_for_user(user_id: str, dataset: Any) -> Optional[str]:
    """
    Get RLS filter for a specific user and dataset.
    
    Args:
        user_id: User identifier
        dataset: Dataset object
        
    Returns:
        SQL filter string or None
    """
    try:
        from .cache_manager import get_user_entitlements
        
        user_entitlements = get_user_entitlements(user_id)
        if not user_entitlements:
            return None
        
        rls_builder = DynamicHierarchicalRLSBuilder()
        return rls_builder.build_filter(user_entitlements, dataset)
        
    except Exception as e:
        logger.error(f"Failed to get RLS filter for user {user_id}: {e}")
        return None


def apply_rls_to_query(query: Any, user_id: str, dataset: Any) -> Any:
    """
    Apply RLS filters to a query for a specific user.
    
    Args:
        query: SQL query
        user_id: User identifier
        dataset: Dataset object
        
    Returns:
        Modified query with RLS applied
    """
    try:
        from .cache_manager import get_user_entitlements
        
        user_entitlements = get_user_entitlements(user_id)
        if not user_entitlements:
            return query
        
        query_builder = RLSQueryBuilder()
        return query_builder.apply_rls_filters(query, user_entitlements, dataset)
        
    except Exception as e:
        logger.error(f"Failed to apply RLS to query for user {user_id}: {e}")
        return query


def validate_rls_configuration() -> bool:
    """
    Validate RLS configuration.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        rls_config = current_app.config.get('RLS_CONFIG', {})
        
        if not rls_config.get('enabled', False):
            logger.warning("RLS is not enabled in configuration")
            return False
        
        hierarchy_registry = get_hierarchy_registry()
        active_hierarchies = hierarchy_registry.get_active_hierarchies()
        
        if not active_hierarchies:
            logger.warning("No active hierarchies found")
            return False
        
        logger.info(f"RLS configuration validated: {len(active_hierarchies)} active hierarchies")
        return True
        
    except Exception as e:
        logger.error(f"RLS configuration validation failed: {e}")
        return False 