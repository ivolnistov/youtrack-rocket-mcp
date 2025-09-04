"""
YouTrack Search Guide - Helper tool for YouTrack query language.
"""

import json

from youtrack_rocket_mcp.api.types import ToolRegistry


class SearchGuide:
    """Guide for YouTrack search query syntax and attributes."""

    async def get_search_syntax_guide(self) -> str:
        """
        Get a comprehensive guide for YouTrack search query syntax.

        Returns:
            JSON string with search syntax guide including all common attributes and examples
        """
        guide = {
            'basic_attributes': {
                'project': {
                    'description': 'Search within specific project(s)',
                    'syntax': 'project: <project_name>',
                    'examples': [
                        'project: MyProject',
                        'project: {My Project}',  # For project names with spaces
                        '#MyProject',  # Short syntax
                        'project: MyProject, AnotherProject',  # Multiple projects
                    ],
                },
                'assignee': {
                    'description': 'Find issues assigned to specific user',
                    'syntax': 'assignee: <username>',
                    'examples': [
                        'assignee: john.doe',
                        'assignee: me',  # Current user
                        'assignee: Unassigned',
                        'assigned to: me',  # Alternative syntax
                    ],
                },
                'reporter': {
                    'description': 'Find issues reported by specific user',
                    'syntax': 'reporter: <username>',
                    'examples': [
                        'reporter: jane.smith',
                        'reporter: me',
                        'reported by: me',  # Alternative syntax
                    ],
                },
                'state': {
                    'description': 'Filter by issue state',
                    'syntax': 'state: <state_name>',
                    'examples': [
                        'state: Open',
                        'state: In Progress',
                        'state: {In Progress}',  # For states with spaces
                        '#Unresolved',  # All unresolved issues
                        '#Resolved',  # All resolved issues
                    ],
                },
                'priority': {
                    'description': 'Filter by priority level',
                    'syntax': 'priority: <priority_name>',
                    'examples': [
                        'priority: Critical',
                        'priority: Show-stopper',
                        'priority: Major',
                        'priority: Normal',
                        'priority: Minor',
                    ],
                },
                'type': {
                    'description': 'Filter by issue type',
                    'syntax': 'type: <type_name>',
                    'examples': [
                        'type: Bug',
                        'type: Feature',
                        'type: Task',
                        'type: {User Story}',  # For types with spaces
                    ],
                },
            },
            'date_attributes': {
                'created': {
                    'description': 'Filter by creation date',
                    'syntax': 'created: <date_range>',
                    'examples': [
                        'created: today',
                        'created: yesterday',
                        'created: {this week}',
                        'created: {this month}',
                        'created: {last week}',
                        'created: 2024-01-01',
                        'created: 2024-01-01 .. 2024-12-31',  # Date range
                        'created: 2024-01-01 ..',  # From date
                        'created: .. 2024-12-31',  # Until date
                    ],
                },
                'updated': {
                    'description': 'Filter by last update date',
                    'syntax': 'updated: <date_range>',
                    'examples': [
                        'updated: today',
                        'updated: {this week}',
                        'updated: {Last 7 days}',
                        'updated: 2024-01-01 .. 2024-01-31',
                    ],
                },
                'resolved': {
                    'description': 'Filter by resolution date',
                    'syntax': 'resolved: <date_range>',
                    'examples': ['resolved: today', 'resolved: {this month}', 'resolved: 2024'],
                },
            },
            'text_search': {
                'description': 'Search in summary and description',
                'examples': [
                    '"exact phrase"',  # Exact phrase search
                    'bug crash',  # All words (AND)
                    'bug or crash',  # Either word (OR)
                    'summary: "login issue"',  # Search only in summary
                    'description: "steps to reproduce"',  # Search only in description
                    'comment: "fixed in version"',  # Search in comments
                ],
            },
            'special_keywords': {
                '#Unresolved': 'All unresolved issues',
                '#Resolved': 'All resolved issues',
                '#Submitted': 'Issues in submitted state',
                '#Open': 'Issues in open state',
                '#InProgress': 'Issues in progress',
                '#Fixed': 'Fixed issues',
                '#Verified': 'Verified issues',
                '#Duplicate': 'Duplicate issues',
                '#WontFix': "Won't fix issues",
                '#CantReproduce': "Can't reproduce issues",
                '#Incomplete': 'Incomplete issues',
                '#Obsolete': 'Obsolete issues',
                '#ByDesign': 'By design issues',
                'has: attachments': 'Issues with attachments',
                'has: comments': 'Issues with comments',
                'has: description': 'Issues with description',
                'has: votes': 'Issues with votes',
                'is: starred': 'Starred issues',
                'is: reported by me': 'Issues reported by current user',
                'is: assigned to me': 'Issues assigned to current user',
            },
            'operators': {
                'AND': {
                    'description': 'Both conditions must be true (default)',
                    'examples': ['project: MyProject state: Open', '#Unresolved priority: Critical'],
                },
                'OR': {
                    'description': 'Either condition must be true',
                    'examples': ['state: Open or state: In Progress', 'priority: Critical or priority: Major'],
                },
                'NOT': {
                    'description': 'Exclude results',
                    'syntax': '-<attribute>',
                    'examples': ['-state: Resolved', '-priority: Minor', 'project: MyProject -assignee: me'],
                },
                'Parentheses': {
                    'description': 'Group conditions',
                    'examples': [
                        '(state: Open or state: In Progress) priority: Critical',
                        'project: MyProject (type: Bug or type: Task)',
                    ],
                },
            },
            'sorting': {
                'description': 'Sort results (when using advanced_search)',
                'examples': [
                    'sort by: created desc',  # In query
                    'sort by: updated asc',
                    'sort by: priority',
                    'sort by: votes',
                ],
                'available_fields': [
                    'created',
                    'updated',
                    'resolved',
                    'priority',
                    'votes',
                    'numberInProject',
                    'summary',
                ],
            },
            'custom_fields': {
                'description': 'Search by custom field values',
                'syntax': '<field_name>: <value>',
                'examples': [
                    'Environment: Production',
                    'Severity: High',
                    'Sprint: {Sprint 23}',
                    'Story Points: 5',
                    'Affected Version: 2.0',
                    'Fix Version: 2.1',
                ],
            },
            'advanced_examples': {
                'complex_queries': [
                    'project: MyProject #Unresolved assignee: me priority: Critical, Major',
                    '#Bug reported by: me updated: {this week} -state: Verified',
                    'project: {My Project} (state: Open or state: {In Progress}) created: {this month}',
                    'assignee: Unassigned type: Bug priority: Critical, Show-stopper',
                    'has: attachments has: comments #Unresolved updated: {Last 7 days}',
                ]
            },
            'tips': [
                'Use curly braces {} for values with spaces',
                'Use quotes "" for exact phrase search',
                'Use # for quick state/tag filters',
                'Combine multiple values with commas (OR logic)',
                "Use 'me' to refer to current user",
                'Date ranges use .. syntax',
                'Negative search with - prefix',
            ],
        }

        return json.dumps(guide, indent=2)

    async def get_common_queries(self) -> str:
        """
        Get a list of common YouTrack search queries for typical use cases.

        Returns:
            JSON string with common query examples organized by use case
        """
        queries = {
            'my_work': {
                'description': 'Queries for personal task management',
                'queries': {
                    'My open issues': 'assignee: me #Unresolved',
                    'Issues I reported': 'reporter: me',
                    'My issues updated today': 'assignee: me updated: today',
                    'My high priority issues': 'assignee: me priority: Critical, Major #Unresolved',
                    'My overdue issues': 'assignee: me #Unresolved Due date: .. today',
                },
            },
            'team_management': {
                'description': 'Queries for team leads and managers',
                'queries': {
                    'Unassigned critical issues': 'assignee: Unassigned priority: Critical #Unresolved',
                    "Team's issues this sprint": 'project: MyProject Sprint: {Current Sprint} #Unresolved',
                    'Recently resolved': 'project: MyProject resolved: {this week}',
                    'Blocked issues': 'project: MyProject state: Blocked',
                    'Issues without estimates': 'project: MyProject Estimation: empty #Unresolved',
                },
            },
            'bug_tracking': {
                'description': 'Queries for QA and bug management',
                'queries': {
                    'Critical bugs': 'type: Bug priority: Critical #Unresolved',
                    'Bugs in production': 'type: Bug Environment: Production #Unresolved',
                    'Bugs to verify': 'type: Bug state: Fixed',
                    'Regression bugs': 'type: Bug tag: regression',
                    'Bugs without reproduction steps': 'type: Bug description: empty',
                },
            },
            'release_planning': {
                'description': 'Queries for release management',
                'queries': {
                    'Issues for next release': 'Fix version: 2.0 #Unresolved',
                    'Completed in version': 'Fix version: 2.0 #Resolved',
                    'No fix version assigned': 'Fix version: empty #Unresolved type: Bug',
                    'Release blockers': 'Fix version: 2.0 priority: Show-stopper #Unresolved',
                },
            },
            'reporting': {
                'description': 'Queries for reports and analytics',
                'queries': {
                    'Created this month': 'created: {this month}',
                    'Resolved this month': 'resolved: {this month}',
                    'Long-standing issues': 'created: .. {6 months ago} #Unresolved',
                    'Most voted issues': '#Unresolved sort by: votes desc',
                    'Recently commented': 'commented: {this week}',
                },
            },
        }

        return json.dumps(queries, indent=2)

    def get_tool_definitions(self) -> ToolRegistry:
        """
        Get the definitions of search guide tools.

        Returns:
            Dictionary mapping tool names to their configuration
        """
        return {
            'get_search_syntax_guide': {
                'function': self.get_search_syntax_guide,
                'description': 'Get a comprehensive guide for YouTrack search query syntax, including all attributes, operators, and examples',
                'parameters': {},
            },
            'get_common_queries': {
                'function': self.get_common_queries,
                'description': 'Get a list of common YouTrack search queries organized by use case (personal work, team management, bug tracking, etc.)',
                'parameters': {},
            },
        }
