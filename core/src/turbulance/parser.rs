/// Turbulance Script Parser
/// 
/// Parses Turbulance domain-specific language scripts into an Abstract Syntax Tree (AST)
/// that can be compiled and executed with semantic understanding.

use anyhow::{Result, Context};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::str::FromStr;

/// Parsed Turbulance script representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedScript {
    /// Script metadata
    pub metadata: ScriptMetadata,
    
    /// Import statements
    pub imports: Vec<ImportStatement>,
    
    /// Hypothesis definitions
    pub hypotheses: Vec<HypothesisDefinition>,
    
    /// Function definitions
    pub functions: Vec<FunctionDefinition>,
    
    /// Proposition definitions
    pub propositions: Vec<PropositionDefinition>,
    
    /// Main execution function
    pub main_function: Option<FunctionDefinition>,
}

/// Import statement for external modules
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportStatement {
    pub module_path: String,
    pub alias: Option<String>,
    pub specific_items: Vec<String>,
}

/// Hypothesis definition with semantic validation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HypothesisDefinition {
    pub name: String,
    pub claim: String,
    pub semantic_validation: HashMap<String, String>,
    pub success_criteria: HashMap<String, f64>,
    pub requirements: Vec<String>,
}

/// Function definition in Turbulance
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FunctionDefinition {
    pub name: String,
    pub parameters: Vec<Parameter>,
    pub return_type: Option<String>,
    pub body: Vec<Statement>,
    pub is_async: bool,
    pub is_main: bool,
}

/// Function parameter
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Parameter {
    pub name: String,
    pub parameter_type: Option<String>,
    pub default_value: Option<Expression>,
}

/// Proposition definition for scientific validation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PropositionDefinition {
    pub name: String,
    pub motions: Vec<Motion>,
    pub validation_blocks: Vec<ValidationBlock>,
}

/// Motion within a proposition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Motion {
    pub name: String,
    pub description: String,
    pub motion_type: MotionType,
}

/// Types of motions in propositions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MotionType {
    SemanticValidation(String),
    ExperimentalValidation(String),
    TheoreticalValidation(String),
    ConsensusValidation(String),
}

/// Validation block within propositions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationBlock {
    pub context: String,
    pub conditions: Vec<Condition>,
    pub actions: Vec<Action>,
}

/// Condition in validation blocks
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Condition {
    pub condition_type: ConditionType,
    pub expression: Expression,
}

/// Types of conditions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConditionType {
    Given,
    When,
    If,
    Unless,
}

/// Action in validation blocks
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Action {
    pub action_type: ActionType,
    pub target: String,
    pub parameters: HashMap<String, Expression>,
}

/// Types of actions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ActionType {
    Support,
    WithConfidence,
    Log,
    Update,
    Print,
    Return,
    Assert,
}

/// Statement in Turbulance
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Statement {
    /// Variable declaration: item name = expression
    ItemDeclaration {
        name: String,
        expression: Expression,
        item_type: Option<String>,
    },
    
    /// Function call: function_name(args)
    FunctionCall {
        function_name: String,
        arguments: Vec<Expression>,
        assignment_target: Option<String>,
    },
    
    /// Method call: object.method(args)
    MethodCall {
        object: Expression,
        method_name: String,
        arguments: Vec<Expression>,
        assignment_target: Option<String>,
    },
    
    /// Print statement
    Print {
        format_string: String,
        arguments: Vec<Expression>,
    },
    
    /// Conditional statement
    Conditional {
        condition: Expression,
        then_block: Vec<Statement>,
        else_block: Option<Vec<Statement>>,
    },
    
    /// Return statement
    Return {
        expression: Option<Expression>,
    },
    
    /// Semantic operation
    SemanticOperation {
        operation_type: String,
        parameters: HashMap<String, Expression>,
    },
    
    /// Loop statement
    Loop {
        loop_type: LoopType,
        body: Vec<Statement>,
    },
}

/// Loop types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LoopType {
    For {
        variable: String,
        iterable: Expression,
    },
    While {
        condition: Expression,
    },
    Considering {
        variable: String,
        collection: Expression,
    },
}

/// Expression in Turbulance
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Expression {
    /// Literal value
    Literal(LiteralValue),
    
    /// Variable reference
    Variable(String),
    
    /// Function call
    FunctionCall {
        function_name: String,
        arguments: Vec<Expression>,
    },
    
    /// Method call
    MethodCall {
        object: Box<Expression>,
        method_name: String,
        arguments: Vec<Expression>,
    },
    
    /// Binary operation
    BinaryOp {
        left: Box<Expression>,
        operator: BinaryOperator,
        right: Box<Expression>,
    },
    
    /// Unary operation
    UnaryOp {
        operator: UnaryOperator,
        operand: Box<Expression>,
    },
    
    /// Dictionary/map literal
    Dictionary {
        entries: Vec<(Expression, Expression)>,
    },
    
    /// Array/list literal
    Array {
        elements: Vec<Expression>,
    },
    
    /// Semantic context expression
    SemanticContext {
        context_type: String,
        parameters: HashMap<String, Expression>,
    },
}

/// Literal values
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LiteralValue {
    String(String),
    Number(f64),
    Integer(i64),
    Boolean(bool),
    Null,
}

/// Binary operators
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BinaryOperator {
    Add,
    Subtract,
    Multiply,
    Divide,
    Modulo,
    Equal,
    NotEqual,
    LessThan,
    LessThanOrEqual,
    GreaterThan,
    GreaterThanOrEqual,
    And,
    Or,
    BitwiseAnd,
    BitwiseOr,
    BitwiseXor,
    LeftShift,
    RightShift,
}

/// Unary operators
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum UnaryOperator {
    Not,
    Minus,
    Plus,
    BitwiseNot,
}

/// Script metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScriptMetadata {
    pub name: String,
    pub description: String,
    pub version: String,
    pub author: String,
    pub scientific_domain: String,
}

/// Turbulance script parser
pub struct TurbulanceParser {
    /// Current parsing position
    position: usize,
    
    /// Source code tokens
    tokens: Vec<Token>,
    
    /// Current token
    current_token: Option<Token>,
}

/// Token types for Turbulance language
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Token {
    // Keywords
    Import,
    Hypothesis,
    Funxn,
    Item,
    Proposition,
    Motion,
    Within,
    Given,
    When,
    If,
    Unless,
    Alternatively,
    Support,
    WithConfidence,
    Considering,
    Print,
    Return,
    For,
    While,
    True,
    False,
    Null,
    
    // Identifiers and literals
    Identifier(String),
    StringLiteral(String),
    NumberLiteral(f64),
    IntegerLiteral(i64),
    
    // Operators
    Plus,
    Minus,
    Multiply,
    Divide,
    Modulo,
    Equal,
    NotEqual,
    LessThan,
    LessThanOrEqual,
    GreaterThan,
    GreaterThanOrEqual,
    And,
    Or,
    Not,
    Assign,
    
    // Delimiters
    LeftParen,
    RightParen,
    LeftBrace,
    RightBrace,
    LeftBracket,
    RightBracket,
    Comma,
    Semicolon,
    Colon,
    Dot,
    Arrow,
    
    // Special
    Newline,
    Whitespace,
    Comment(String),
    EndOfFile,
}

impl TurbulanceParser {
    /// Parse Turbulance script from source code
    pub fn parse(source_code: &str) -> Result<ParsedScript> {
        let mut parser = TurbulanceParser::new(source_code)?;
        parser.parse_script()
    }
    
    /// Create a new parser
    fn new(source_code: &str) -> Result<Self> {
        let tokens = TurbulanceParser::tokenize(source_code)?;
        let mut parser = TurbulanceParser {
            position: 0,
            tokens,
            current_token: None,
        };
        
        parser.advance();
        Ok(parser)
    }
    
    /// Tokenize source code
    fn tokenize(source_code: &str) -> Result<Vec<Token>> {
        let mut tokens = Vec::new();
        let mut chars = source_code.chars().peekable();
        
        while let Some(ch) = chars.next() {
            match ch {
                // Whitespace
                ' ' | '\t' | '\r' => {
                    tokens.push(Token::Whitespace);
                }
                '\n' => {
                    tokens.push(Token::Newline);
                }
                
                // Comments
                '/' if chars.peek() == Some(&'/') => {
                    chars.next(); // consume second '/'
                    let mut comment = String::new();
                    while let Some(ch) = chars.next() {
                        if ch == '\n' {
                            break;
                        }
                        comment.push(ch);
                    }
                    tokens.push(Token::Comment(comment));
                    tokens.push(Token::Newline);
                }
                
                // String literals
                '"' => {
                    let mut string_value = String::new();
                    let mut escaped = false;
                    
                    while let Some(ch) = chars.next() {
                        if escaped {
                            match ch {
                                'n' => string_value.push('\n'),
                                't' => string_value.push('\t'),
                                'r' => string_value.push('\r'),
                                '\\' => string_value.push('\\'),
                                '"' => string_value.push('"'),
                                _ => {
                                    string_value.push('\\');
                                    string_value.push(ch);
                                }
                            }
                            escaped = false;
                        } else if ch == '\\' {
                            escaped = true;
                        } else if ch == '"' {
                            break;
                        } else {
                            string_value.push(ch);
                        }
                    }
                    
                    tokens.push(Token::StringLiteral(string_value));
                }
                
                // Numbers
                '0'..='9' => {
                    let mut number_str = String::new();
                    number_str.push(ch);
                    
                    let mut is_float = false;
                    while let Some(&next_ch) = chars.peek() {
                        if next_ch.is_ascii_digit() {
                            number_str.push(chars.next().unwrap());
                        } else if next_ch == '.' && !is_float {
                            is_float = true;
                            number_str.push(chars.next().unwrap());
                        } else {
                            break;
                        }
                    }
                    
                    if is_float {
                        let value = number_str.parse::<f64>()
                            .context("Failed to parse float literal")?;
                        tokens.push(Token::NumberLiteral(value));
                    } else {
                        let value = number_str.parse::<i64>()
                            .context("Failed to parse integer literal")?;
                        tokens.push(Token::IntegerLiteral(value));
                    }
                }
                
                // Identifiers and keywords
                'a'..='z' | 'A'..='Z' | '_' => {
                    let mut identifier = String::new();
                    identifier.push(ch);
                    
                    while let Some(&next_ch) = chars.peek() {
                        if next_ch.is_alphanumeric() || next_ch == '_' {
                            identifier.push(chars.next().unwrap());
                        } else {
                            break;
                        }
                    }
                    
                    let token = match identifier.as_str() {
                        "import" => Token::Import,
                        "hypothesis" => Token::Hypothesis,
                        "funxn" => Token::Funxn,
                        "item" => Token::Item,
                        "proposition" => Token::Proposition,
                        "motion" => Token::Motion,
                        "within" => Token::Within,
                        "given" => Token::Given,
                        "when" => Token::When,
                        "if" => Token::If,
                        "unless" => Token::Unless,
                        "alternatively" => Token::Alternatively,
                        "support" => Token::Support,
                        "with_confidence" => Token::WithConfidence,
                        "considering" => Token::Considering,
                        "print" => Token::Print,
                        "return" => Token::Return,
                        "for" => Token::For,
                        "while" => Token::While,
                        "true" => Token::True,
                        "false" => Token::False,
                        "null" => Token::Null,
                        _ => Token::Identifier(identifier),
                    };
                    tokens.push(token);
                }
                
                // Operators and delimiters
                '+' => tokens.push(Token::Plus),
                '-' => {
                    if chars.peek() == Some(&'>') {
                        chars.next();
                        tokens.push(Token::Arrow);
                    } else {
                        tokens.push(Token::Minus);
                    }
                }
                '*' => tokens.push(Token::Multiply),
                '/' => tokens.push(Token::Divide),
                '%' => tokens.push(Token::Modulo),
                '=' => {
                    if chars.peek() == Some(&'=') {
                        chars.next();
                        tokens.push(Token::Equal);
                    } else {
                        tokens.push(Token::Assign);
                    }
                }
                '!' => {
                    if chars.peek() == Some(&'=') {
                        chars.next();
                        tokens.push(Token::NotEqual);
                    } else {
                        tokens.push(Token::Not);
                    }
                }
                '<' => {
                    if chars.peek() == Some(&'=') {
                        chars.next();
                        tokens.push(Token::LessThanOrEqual);
                    } else {
                        tokens.push(Token::LessThan);
                    }
                }
                '>' => {
                    if chars.peek() == Some(&'=') {
                        chars.next();
                        tokens.push(Token::GreaterThanOrEqual);
                    } else {
                        tokens.push(Token::GreaterThan);
                    }
                }
                '&' => {
                    if chars.peek() == Some(&'&') {
                        chars.next();
                        tokens.push(Token::And);
                    }
                }
                '|' => {
                    if chars.peek() == Some(&'|') {
                        chars.next();
                        tokens.push(Token::Or);
                    }
                }
                '(' => tokens.push(Token::LeftParen),
                ')' => tokens.push(Token::RightParen),
                '{' => tokens.push(Token::LeftBrace),
                '}' => tokens.push(Token::RightBrace),
                '[' => tokens.push(Token::LeftBracket),
                ']' => tokens.push(Token::RightBracket),
                ',' => tokens.push(Token::Comma),
                ';' => tokens.push(Token::Semicolon),
                ':' => tokens.push(Token::Colon),
                '.' => tokens.push(Token::Dot),
                
                _ => {
                    return Err(anyhow::anyhow!("Unexpected character: {}", ch));
                }
            }
        }
        
        tokens.push(Token::EndOfFile);
        Ok(tokens)
    }
    
    /// Parse the complete script
    fn parse_script(&mut self) -> Result<ParsedScript> {
        let mut imports = Vec::new();
        let mut hypotheses = Vec::new();
        let mut functions = Vec::new();
        let mut propositions = Vec::new();
        let mut main_function = None;
        
        // Skip whitespace and comments
        self.skip_whitespace();
        
        while !self.is_at_end() {
            match &self.current_token {
                Some(Token::Import) => {
                    imports.push(self.parse_import()?);
                }
                Some(Token::Hypothesis) => {
                    hypotheses.push(self.parse_hypothesis()?);
                }
                Some(Token::Funxn) => {
                    let function = self.parse_function()?;
                    if function.name == "main" || function.is_main {
                        main_function = Some(function);
                    } else {
                        functions.push(function);
                    }
                }
                Some(Token::Proposition) => {
                    propositions.push(self.parse_proposition()?);
                }
                Some(Token::Comment(_)) | Some(Token::Newline) | Some(Token::Whitespace) => {
                    self.advance();
                }
                _ => {
                    return Err(anyhow::anyhow!("Unexpected token at top level: {:?}", self.current_token));
                }
            }
            
            self.skip_whitespace();
        }
        
        Ok(ParsedScript {
            metadata: ScriptMetadata {
                name: "Parsed Script".to_string(),
                description: "Parsed Turbulance script".to_string(),
                version: "1.0.0".to_string(),
                author: "Unknown".to_string(),
                scientific_domain: "General".to_string(),
            },
            imports,
            hypotheses,
            functions,
            propositions,
            main_function,
        })
    }
    
    /// Parse import statement
    fn parse_import(&mut self) -> Result<ImportStatement> {
        self.expect(Token::Import)?;
        
        let module_path = match &self.current_token {
            Some(Token::Identifier(path)) => {
                let path = path.clone();
                self.advance();
                path
            }
            _ => return Err(anyhow::anyhow!("Expected module path after import")),
        };
        
        self.skip_whitespace();
        
        Ok(ImportStatement {
            module_path,
            alias: None,
            specific_items: Vec::new(),
        })
    }
    
    /// Parse hypothesis definition
    fn parse_hypothesis(&mut self) -> Result<HypothesisDefinition> {
        self.expect(Token::Hypothesis)?;
        
        let name = self.expect_identifier()?;
        self.expect(Token::Colon)?;
        self.skip_whitespace();
        
        let mut claim = String::new();
        let mut semantic_validation = HashMap::new();
        let mut success_criteria = HashMap::new();
        let mut requirements = Vec::new();
        
        // Parse hypothesis body
        while !self.is_at_end() && !matches!(self.current_token, Some(Token::Funxn) | Some(Token::Proposition) | Some(Token::Hypothesis)) {
            match &self.current_token {
                Some(Token::Identifier(key)) => {
                    let key = key.clone();
                    self.advance();
                    self.expect(Token::Colon)?;
                    
                    match key.as_str() {
                        "claim" => {
                            claim = self.expect_string_literal()?;
                        }
                        "requires" => {
                            requirements.push(self.expect_string_literal()?);
                        }
                        _ => {
                            // Parse as semantic validation or success criteria
                            let value = self.expect_string_literal()?;
                            semantic_validation.insert(key, value);
                        }
                    }
                }
                _ => self.advance(),
            }
            self.skip_whitespace();
        }
        
        Ok(HypothesisDefinition {
            name,
            claim,
            semantic_validation,
            success_criteria,
            requirements,
        })
    }
    
    /// Parse function definition
    fn parse_function(&mut self) -> Result<FunctionDefinition> {
        self.expect(Token::Funxn)?;
        
        let name = self.expect_identifier()?;
        self.expect(Token::LeftParen)?;
        
        let mut parameters = Vec::new();
        
        // Parse parameters
        while !matches!(self.current_token, Some(Token::RightParen)) {
            let param_name = self.expect_identifier()?;
            
            // Optional type annotation
            let param_type = if matches!(self.current_token, Some(Token::Colon)) {
                self.advance();
                Some(self.expect_identifier()?)
            } else {
                None
            };
            
            parameters.push(Parameter {
                name: param_name,
                parameter_type: param_type,
                default_value: None,
            });
            
            if matches!(self.current_token, Some(Token::Comma)) {
                self.advance();
            }
        }
        
        self.expect(Token::RightParen)?;
        self.expect(Token::Colon)?;
        self.skip_whitespace();
        
        // Parse function body
        let body = self.parse_block()?;
        
        Ok(FunctionDefinition {
            name: name.clone(),
            parameters,
            return_type: None,
            body,
            is_async: false,
            is_main: name == "main",
        })
    }
    
    /// Parse proposition definition
    fn parse_proposition(&mut self) -> Result<PropositionDefinition> {
        self.expect(Token::Proposition)?;
        
        let name = self.expect_identifier()?;
        self.expect(Token::Colon)?;
        self.skip_whitespace();
        
        let mut motions = Vec::new();
        let mut validation_blocks = Vec::new();
        
        // Parse proposition body
        while !self.is_at_end() && !matches!(self.current_token, Some(Token::Funxn) | Some(Token::Proposition) | Some(Token::Hypothesis)) {
            match &self.current_token {
                Some(Token::Motion) => {
                    motions.push(self.parse_motion()?);
                }
                Some(Token::Within) => {
                    validation_blocks.push(self.parse_validation_block()?);
                }
                _ => self.advance(),
            }
            self.skip_whitespace();
        }
        
        Ok(PropositionDefinition {
            name,
            motions,
            validation_blocks,
        })
    }
    
    /// Parse motion
    fn parse_motion(&mut self) -> Result<Motion> {
        self.expect(Token::Motion)?;
        
        let name = self.expect_identifier()?;
        self.expect(Token::LeftParen)?;
        let description = self.expect_string_literal()?;
        self.expect(Token::RightParen)?;
        
        Ok(Motion {
            name,
            description,
            motion_type: MotionType::SemanticValidation("default".to_string()),
        })
    }
    
    /// Parse validation block
    fn parse_validation_block(&mut self) -> Result<ValidationBlock> {
        self.expect(Token::Within)?;
        
        let context = self.expect_identifier()?;
        self.expect(Token::Colon)?;
        self.skip_whitespace();
        
        let mut conditions = Vec::new();
        let mut actions = Vec::new();
        
        // Parse validation block body
        while !self.is_at_end() && !matches!(self.current_token, Some(Token::Within) | Some(Token::Funxn) | Some(Token::Proposition)) {
            match &self.current_token {
                Some(Token::Given) => {
                    conditions.push(self.parse_condition(ConditionType::Given)?);
                }
                Some(Token::Support) => {
                    actions.push(self.parse_action(ActionType::Support)?);
                }
                Some(Token::Print) => {
                    actions.push(self.parse_action(ActionType::Print)?);
                }
                _ => self.advance(),
            }
            self.skip_whitespace();
        }
        
        Ok(ValidationBlock {
            context,
            conditions,
            actions,
        })
    }
    
    /// Parse condition
    fn parse_condition(&mut self, condition_type: ConditionType) -> Result<Condition> {
        match condition_type {
            ConditionType::Given => self.expect(Token::Given)?,
            _ => {}
        }
        
        let expression = self.parse_expression()?;
        
        Ok(Condition {
            condition_type,
            expression,
        })
    }
    
    /// Parse action
    fn parse_action(&mut self, action_type: ActionType) -> Result<Action> {
        match action_type {
            ActionType::Support => {
                self.expect(Token::Support)?;
                let target = self.expect_identifier()?;
                Ok(Action {
                    action_type,
                    target,
                    parameters: HashMap::new(),
                })
            }
            ActionType::Print => {
                self.expect(Token::Print)?;
                self.expect(Token::LeftParen)?;
                let format_string = self.expect_string_literal()?;
                self.expect(Token::RightParen)?;
                
                let mut parameters = HashMap::new();
                parameters.insert("format".to_string(), Expression::Literal(LiteralValue::String(format_string)));
                
                Ok(Action {
                    action_type,
                    target: "console".to_string(),
                    parameters,
                })
            }
            _ => {
                Ok(Action {
                    action_type,
                    target: String::new(),
                    parameters: HashMap::new(),
                })
            }
        }
    }
    
    /// Parse block of statements
    fn parse_block(&mut self) -> Result<Vec<Statement>> {
        let mut statements = Vec::new();
        
        while !self.is_at_end() && !matches!(self.current_token, Some(Token::Funxn) | Some(Token::Proposition) | Some(Token::Hypothesis)) {
            if let Some(statement) = self.parse_statement()? {
                statements.push(statement);
            }
            self.skip_whitespace();
        }
        
        Ok(statements)
    }
    
    /// Parse statement
    fn parse_statement(&mut self) -> Result<Option<Statement>> {
        match &self.current_token {
            Some(Token::Item) => {
                self.advance();
                let name = self.expect_identifier()?;
                self.expect(Token::Assign)?;
                let expression = self.parse_expression()?;
                
                Ok(Some(Statement::ItemDeclaration {
                    name,
                    expression,
                    item_type: None,
                }))
            }
            Some(Token::Print) => {
                self.advance();
                self.expect(Token::LeftParen)?;
                let format_string = self.expect_string_literal()?;
                
                let mut arguments = Vec::new();
                while matches!(self.current_token, Some(Token::Comma)) {
                    self.advance();
                    arguments.push(self.parse_expression()?);
                }
                
                self.expect(Token::RightParen)?;
                
                Ok(Some(Statement::Print {
                    format_string,
                    arguments,
                }))
            }
            Some(Token::Return) => {
                self.advance();
                let expression = if matches!(self.current_token, Some(Token::Newline) | Some(Token::EndOfFile)) {
                    None
                } else {
                    Some(self.parse_expression()?)
                };
                
                Ok(Some(Statement::Return { expression }))
            }
            Some(Token::Identifier(_)) => {
                // Could be function call or assignment
                let identifier = self.expect_identifier()?;
                
                if matches!(self.current_token, Some(Token::LeftParen)) {
                    // Function call
                    self.advance();
                    let mut arguments = Vec::new();
                    
                    while !matches!(self.current_token, Some(Token::RightParen)) {
                        arguments.push(self.parse_expression()?);
                        if matches!(self.current_token, Some(Token::Comma)) {
                            self.advance();
                        }
                    }
                    
                    self.expect(Token::RightParen)?;
                    
                    Ok(Some(Statement::FunctionCall {
                        function_name: identifier,
                        arguments,
                        assignment_target: None,
                    }))
                } else {
                    // Skip for now
                    Ok(None)
                }
            }
            Some(Token::Comment(_)) | Some(Token::Newline) | Some(Token::Whitespace) => {
                self.advance();
                Ok(None)
            }
            _ => Ok(None),
        }
    }
    
    /// Parse expression
    fn parse_expression(&mut self) -> Result<Expression> {
        self.parse_binary_expression(0)
    }
    
    /// Parse binary expression with precedence
    fn parse_binary_expression(&mut self, min_precedence: u8) -> Result<Expression> {
        let mut left = self.parse_primary_expression()?;
        
        while let Some(token) = &self.current_token {
            let (operator, precedence) = match token {
                Token::Plus => (BinaryOperator::Add, 1),
                Token::Minus => (BinaryOperator::Subtract, 1),
                Token::Multiply => (BinaryOperator::Multiply, 2),
                Token::Divide => (BinaryOperator::Divide, 2),
                Token::Equal => (BinaryOperator::Equal, 3),
                Token::NotEqual => (BinaryOperator::NotEqual, 3),
                Token::LessThan => (BinaryOperator::LessThan, 3),
                Token::GreaterThan => (BinaryOperator::GreaterThan, 3),
                Token::And => (BinaryOperator::And, 4),
                Token::Or => (BinaryOperator::Or, 5),
                _ => break,
            };
            
            if precedence < min_precedence {
                break;
            }
            
            self.advance();
            let right = self.parse_binary_expression(precedence + 1)?;
            
            left = Expression::BinaryOp {
                left: Box::new(left),
                operator,
                right: Box::new(right),
            };
        }
        
        Ok(left)
    }
    
    /// Parse primary expression
    fn parse_primary_expression(&mut self) -> Result<Expression> {
        match &self.current_token {
            Some(Token::StringLiteral(s)) => {
                let value = s.clone();
                self.advance();
                Ok(Expression::Literal(LiteralValue::String(value)))
            }
            Some(Token::NumberLiteral(n)) => {
                let value = *n;
                self.advance();
                Ok(Expression::Literal(LiteralValue::Number(value)))
            }
            Some(Token::IntegerLiteral(i)) => {
                let value = *i;
                self.advance();
                Ok(Expression::Literal(LiteralValue::Integer(value)))
            }
            Some(Token::True) => {
                self.advance();
                Ok(Expression::Literal(LiteralValue::Boolean(true)))
            }
            Some(Token::False) => {
                self.advance();
                Ok(Expression::Literal(LiteralValue::Boolean(false)))
            }
            Some(Token::Null) => {
                self.advance();
                Ok(Expression::Literal(LiteralValue::Null))
            }
            Some(Token::Identifier(name)) => {
                let name = name.clone();
                self.advance();
                
                if matches!(self.current_token, Some(Token::LeftParen)) {
                    // Function call
                    self.advance();
                    let mut arguments = Vec::new();
                    
                    while !matches!(self.current_token, Some(Token::RightParen)) {
                        arguments.push(self.parse_expression()?);
                        if matches!(self.current_token, Some(Token::Comma)) {
                            self.advance();
                        }
                    }
                    
                    self.expect(Token::RightParen)?;
                    
                    Ok(Expression::FunctionCall {
                        function_name: name,
                        arguments,
                    })
                } else {
                    Ok(Expression::Variable(name))
                }
            }
            Some(Token::LeftParen) => {
                self.advance();
                let expr = self.parse_expression()?;
                self.expect(Token::RightParen)?;
                Ok(expr)
            }
            _ => Err(anyhow::anyhow!("Unexpected token in expression: {:?}", self.current_token)),
        }
    }
    
    // Helper methods
    fn advance(&mut self) {
        if self.position < self.tokens.len() {
            self.current_token = Some(self.tokens[self.position].clone());
            self.position += 1;
        } else {
            self.current_token = Some(Token::EndOfFile);
        }
    }
    
    fn skip_whitespace(&mut self) {
        while matches!(self.current_token, Some(Token::Whitespace) | Some(Token::Newline) | Some(Token::Comment(_))) {
            self.advance();
        }
    }
    
    fn is_at_end(&self) -> bool {
        matches!(self.current_token, Some(Token::EndOfFile))
    }
    
    fn expect(&mut self, expected: Token) -> Result<()> {
        if std::mem::discriminant(&self.current_token.as_ref().unwrap()) == std::mem::discriminant(&expected) {
            self.advance();
            Ok(())
        } else {
            Err(anyhow::anyhow!("Expected {:?}, found {:?}", expected, self.current_token))
        }
    }
    
    fn expect_identifier(&mut self) -> Result<String> {
        match &self.current_token {
            Some(Token::Identifier(name)) => {
                let name = name.clone();
                self.advance();
                Ok(name)
            }
            _ => Err(anyhow::anyhow!("Expected identifier, found {:?}", self.current_token)),
        }
    }
    
    fn expect_string_literal(&mut self) -> Result<String> {
        match &self.current_token {
            Some(Token::StringLiteral(s)) => {
                let s = s.clone();
                self.advance();
                Ok(s)
            }
            _ => Err(anyhow::anyhow!("Expected string literal, found {:?}", self.current_token)),
        }
    }
} 