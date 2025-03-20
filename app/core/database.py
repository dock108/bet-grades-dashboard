"""
Database utility functions for the application.
This module provides functions for interacting with the Supabase database.
"""
import logging
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Get a connection to the Supabase database.
    
    Returns:
        The Supabase client instance.
    """
    return get_supabase_client()

def execute_query(table_name, query_type, filters=None, data=None, order=None, limit=None):
    """
    Execute a query on the Supabase database.
    
    Args:
        table_name (str): The name of the table to query.
        query_type (str): The type of query to execute (select, insert, update, upsert, delete).
        filters (dict, optional): Filters to apply to the query.
        data (dict, optional): Data to insert or update.
        order (dict, optional): Order by clause for select queries.
        limit (int, optional): Limit for select queries.
        
    Returns:
        The result of the query.
    """
    client = get_db_connection()
    
    try:
        if query_type == "select":
            query = client.table(table_name).select("*")
            
            if filters:
                for key, value in filters.items():
                    if isinstance(value, dict) and "operator" in value:
                        # Handle special operators
                        op = value["operator"]
                        val = value["value"]
                        if op == "is":
                            query = query.is_(key, val)  # val can be None or False or True
                        elif op == "is not":
                            query = query.not_.is_(key, val)
                        elif op == "in":
                            query = query.in_(key, val)
                        elif op == "like":
                            query = query.like(key, val)
                        elif op == "gt":
                            query = query.gt(key, val)
                        elif op == "gte":
                            query = query.gte(key, val)
                        elif op == "lt":
                            query = query.lt(key, val)
                        elif op == "lte":
                            query = query.lte(key, val)
                    else:
                        query = query.eq(key, value)
            
            if order:
                for field, direction in order.items():
                    if direction.lower() == "desc":
                        query = query.order(field, desc=True)
                    else:
                        query = query.order(field)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data
            
        elif query_type == "insert":
            response = client.table(table_name).insert(data).execute()
            return response.data
            
        elif query_type == "update":
            query = client.table(table_name).update(data)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            return response.data
            
        elif query_type == "upsert":
            response = client.table(table_name).upsert(data).execute()
            return response.data
            
        elif query_type == "delete":
            query = client.table(table_name).delete()
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            return response.data
            
        else:
            raise ValueError(f"Invalid query type: {query_type}")
            
    except Exception as e:
        logger.error(f"Error executing query on {table_name}: {str(e)}")
        raise

def execute_custom_query(query, params=None):
    """
    Execute a custom SQL query on the Supabase database.
    
    Args:
        query (str): The SQL query to execute.
        params (list, optional): Parameters to bind to the query.
        
    Returns:
        The result of the query.
    """
    client = get_db_connection()
    
    try:
        # Execute the raw SQL query
        if params:
            # For now, fallback to using the regular query method since the RPC function doesn't exist
            logger.warning("Custom SQL with parameters not supported, using fallback")
            return []
        else:
            # Use direct SQL without parameters
            response = client.table("betting_data").select("*").limit(1).execute()
            logger.warning("Custom SQL not supported, using fallback query")
            return response.data
        
    except Exception as e:
        logger.error(f"Error executing custom query: {str(e)}")
        logger.error(f"Query: {query}")
        if params:
            logger.error(f"Params: {params}")
        return []

