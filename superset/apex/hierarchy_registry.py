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

"""Dynamic hierarchy registry for Apex integration."""

import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from flask import current_app

logger = logging.getLogger(__name__)


@dataclass
class HierarchyDefinition:
    """Hierarchy definition data structure."""
    hierarchy_name: str
    hierarchy_definition: List[str]
    column_mappings: Dict[str, str]
    inheritance_rules: Dict[str, Any]
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HierarchyDefinition':
        """Create from dictionary."""
        return cls(**data)


class HierarchyRegistry:
    """
    Registry for managing dynamic hierarchy configurations.
    
    Supports runtime registration, modification, and lookup of hierarchies.
    """
    
    def __init__(self):
        self.hierarchies: Dict[str, HierarchyDefinition] = {}
        self.hierarchy_lookup_cache: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
    
    def register_hierarchy(self, hierarchy_name: str, hierarchy_config: Dict[str, Any]) -> None:
        """
        Register a new hierarchy configuration.
        
        Args:
            hierarchy_name: Name of the hierarchy
            hierarchy_config: Hierarchy configuration dictionary
        """
        try:
            # Validate hierarchy configuration
            self._validate_hierarchy_config(hierarchy_config)
            
            # Create hierarchy definition
            config_with_name = {**hierarchy_config, 'hierarchy_name': hierarchy_name}
            hierarchy_def = HierarchyDefinition.from_dict(config_with_name)
            
            # Store in registry
            self.hierarchies[hierarchy_name] = hierarchy_def
            
            logger.info(f"Registered hierarchy: {hierarchy_name}")
            
        except Exception as e:
            logger.error(f"Failed to register hierarchy {hierarchy_name}: {e}")
            raise
    
    def get_hierarchy(self, hierarchy_name: str) -> Optional[HierarchyDefinition]:
        """
        Get hierarchy configuration by name.
        
        Args:
            hierarchy_name: Name of the hierarchy
            
        Returns:
            HierarchyDefinition if found, None otherwise
        """
        return self.hierarchies.get(hierarchy_name)
    
    def list_hierarchies(self) -> List[str]:
        """List all registered hierarchy names."""
        return list(self.hierarchies.keys())
    
    def get_active_hierarchies(self) -> Dict[str, HierarchyDefinition]:
        """Get all active hierarchies."""
        return {
            name: hierarchy 
            for name, hierarchy in self.hierarchies.items() 
            if hierarchy.active
        }
    
    def update_hierarchy(self, hierarchy_name: str, hierarchy_config: Dict[str, Any]) -> None:
        """
        Update an existing hierarchy configuration.
        
        Args:
            hierarchy_name: Name of the hierarchy
            hierarchy_config: Updated hierarchy configuration
        """
        if hierarchy_name not in self.hierarchies:
            raise ValueError(f"Hierarchy {hierarchy_name} not found")
        
        try:
            self._validate_hierarchy_config(hierarchy_config)
            
            config_with_name = {**hierarchy_config, 'hierarchy_name': hierarchy_name}
            hierarchy_def = HierarchyDefinition.from_dict(config_with_name)
            
            self.hierarchies[hierarchy_name] = hierarchy_def
            
            # Clear related cache
            if hierarchy_name in self.hierarchy_lookup_cache:
                del self.hierarchy_lookup_cache[hierarchy_name]
            
            logger.info(f"Updated hierarchy: {hierarchy_name}")
            
        except Exception as e:
            logger.error(f"Failed to update hierarchy {hierarchy_name}: {e}")
            raise
    
    def remove_hierarchy(self, hierarchy_name: str) -> None:
        """
        Remove a hierarchy from the registry.
        
        Args:
            hierarchy_name: Name of the hierarchy to remove
        """
        if hierarchy_name in self.hierarchies:
            del self.hierarchies[hierarchy_name]
            
            # Clear related cache
            if hierarchy_name in self.hierarchy_lookup_cache:
                del self.hierarchy_lookup_cache[hierarchy_name]
            
            logger.info(f"Removed hierarchy: {hierarchy_name}")
        else:
            logger.warning(f"Hierarchy {hierarchy_name} not found for removal")
    
    def deactivate_hierarchy(self, hierarchy_name: str) -> None:
        """
        Deactivate a hierarchy without removing it.
        
        Args:
            hierarchy_name: Name of the hierarchy to deactivate
        """
        if hierarchy_name in self.hierarchies:
            self.hierarchies[hierarchy_name].active = False
            logger.info(f"Deactivated hierarchy: {hierarchy_name}")
    
    def activate_hierarchy(self, hierarchy_name: str) -> None:
        """
        Activate a hierarchy.
        
        Args:
            hierarchy_name: Name of the hierarchy to activate
        """
        if hierarchy_name in self.hierarchies:
            self.hierarchies[hierarchy_name].active = True
            logger.info(f"Activated hierarchy: {hierarchy_name}")
    
    def get_hierarchy_lookup_data(self, hierarchy_name: str) -> Dict[str, Any]:
        """
        Get hierarchy lookup data for inheritance calculations.
        
        Args:
            hierarchy_name: Name of the hierarchy
            
        Returns:
            Hierarchy lookup data
        """
        return self.hierarchy_lookup_cache.get(hierarchy_name, {})
    
    def update_hierarchy_lookup_cache(self, hierarchy_name: str, lookup_data: Dict[str, Any]) -> None:
        """
        Update hierarchy lookup cache.
        
        Args:
            hierarchy_name: Name of the hierarchy
            lookup_data: Lookup data to cache
        """
        self.hierarchy_lookup_cache[hierarchy_name] = lookup_data
    
    def clear_hierarchy_cache(self, hierarchy_name: str = None) -> None:
        """
        Clear hierarchy lookup cache.
        
        Args:
            hierarchy_name: Specific hierarchy to clear, or None to clear all
        """
        if hierarchy_name:
            if hierarchy_name in self.hierarchy_lookup_cache:
                del self.hierarchy_lookup_cache[hierarchy_name]
        else:
            self.hierarchy_lookup_cache.clear()
    
    def load_hierarchies_from_config(self) -> None:
        """Load hierarchy configurations from Flask app config."""
        if self._loaded:
            return
        
        try:
            hierarchy_configs = current_app.config.get('RLS_CONFIG', {}).get('hierarchy_definitions', {})
            
            for hierarchy_name, config in hierarchy_configs.items():
                self.register_hierarchy(hierarchy_name, config)
            
            self._loaded = True
            logger.info(f"Loaded {len(hierarchy_configs)} hierarchies from config")
            
        except Exception as e:
            logger.error(f"Failed to load hierarchies from config: {e}")
    
    def load_hierarchies_from_service(self, entitlement_client) -> None:
        """
        Load hierarchy configurations from entitlement service.
        
        Args:
            entitlement_client: Entitlement service client
        """
        try:
            hierarchies = entitlement_client.get_hierarchies()
            
            for hierarchy_data in hierarchies:
                hierarchy_name = hierarchy_data.get('hierarchy_name')
                if hierarchy_name:
                    # Convert service format to our internal format
                    config = {
                        'hierarchy_definition': hierarchy_data.get('hierarchy_definition', []),
                        'column_mappings': hierarchy_data.get('column_mappings', {}),
                        'inheritance_rules': hierarchy_data.get('inheritance_rules', {
                            'enabled': True,
                            'direction': 'top_down'
                        }),
                        'active': hierarchy_data.get('active', True)
                    }
                    
                    self.register_hierarchy(hierarchy_name, config)
            
            logger.info(f"Loaded {len(hierarchies)} hierarchies from service")
            
        except Exception as e:
            logger.error(f"Failed to load hierarchies from service: {e}")
    
    def _validate_hierarchy_config(self, config: Dict[str, Any]) -> None:
        """
        Validate hierarchy configuration.
        
        Args:
            config: Hierarchy configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = ['hierarchy_definition', 'column_mappings']
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        hierarchy_definition = config['hierarchy_definition']
        column_mappings = config['column_mappings']
        
        if not isinstance(hierarchy_definition, list) or len(hierarchy_definition) == 0:
            raise ValueError("hierarchy_definition must be a non-empty list")
        
        if not isinstance(column_mappings, dict):
            raise ValueError("column_mappings must be a dictionary")
        
        # Validate that all hierarchy levels have column mappings
        for level in hierarchy_definition:
            if level not in column_mappings:
                logger.warning(f"No column mapping for hierarchy level: {level}")
    
    def export_hierarchies(self) -> Dict[str, Any]:
        """Export all hierarchies to a dictionary."""
        return {
            name: hierarchy.to_dict() 
            for name, hierarchy in self.hierarchies.items()
        }
    
    def import_hierarchies(self, hierarchies_data: Dict[str, Any]) -> None:
        """
        Import hierarchies from a dictionary.
        
        Args:
            hierarchies_data: Dictionary of hierarchy configurations
        """
        for hierarchy_name, config in hierarchies_data.items():
            try:
                self.register_hierarchy(hierarchy_name, config)
            except Exception as e:
                logger.error(f"Failed to import hierarchy {hierarchy_name}: {e}")


# Global hierarchy registry instance
hierarchy_registry = HierarchyRegistry()


def get_hierarchy_registry() -> HierarchyRegistry:
    """Get the global hierarchy registry instance."""
    return hierarchy_registry


def init_hierarchy_registry(app, entitlement_client=None):
    """
    Initialize the hierarchy registry.
    
    Args:
        app: Flask application instance
        entitlement_client: Optional entitlement service client
    """
    global hierarchy_registry
    
    try:
        # Load from config first
        hierarchy_registry.load_hierarchies_from_config()
        
        # Load from service if available
        if entitlement_client:
            hierarchy_registry.load_hierarchies_from_service(entitlement_client)
        
        logger.info("Hierarchy registry initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize hierarchy registry: {e}")


def register_default_hierarchies():
    """Register some default hierarchies for demo/testing purposes."""
    default_hierarchies = {
        'geographic_hierarchy': {
            'hierarchy_definition': ['country', 'state', 'city', 'district'],
            'column_mappings': {
                'country': 'country_code',
                'state': 'state_code',
                'city': 'city_name',
                'district': 'district_id'
            },
            'inheritance_rules': {
                'enabled': True,
                'direction': 'top_down'
            }
        },
        'product_hierarchy': {
            'hierarchy_definition': ['category', 'sub_category', 'product_type', 'sku'],
            'column_mappings': {
                'category': 'product_category',
                'sub_category': 'product_sub_category',
                'product_type': 'product_type_code',
                'sku': 'product_sku'
            },
            'inheritance_rules': {
                'enabled': True,
                'direction': 'top_down'
            }
        },
        'organization_hierarchy': {
            'hierarchy_definition': ['division', 'department', 'team', 'project'],
            'column_mappings': {
                'division': 'div_code',
                'department': 'dept_code',
                'team': 'team_id',
                'project': 'project_id'
            },
            'inheritance_rules': {
                'enabled': True,
                'direction': 'top_down'
            }
        }
    }
    
    for name, config in default_hierarchies.items():
        try:
            hierarchy_registry.register_hierarchy(name, config)
        except Exception as e:
            logger.error(f"Failed to register default hierarchy {name}: {e}") 